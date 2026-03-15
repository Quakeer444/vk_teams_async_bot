"""Bot class -- main entry point for the VK Teams async bot."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any, Callable, Awaitable, Sequence

from .client.retry import RetryPolicy
from .client.session import VKTeamsSession
from .dispatcher import Dispatcher
from .errors import PollingError
from .fsm.storage.base import BaseStorage
from .methods.chats import ChatMethods
from .methods.events import EventMethods
from .methods.files import FileMethods
from .methods.messages import MessageMethods
from .methods.self_ import SelfMethods
from .types.event import BaseEvent, RawUnknownEvent

logger = logging.getLogger(__name__)

LifecycleHook = Callable[["Bot"], Awaitable[None]]


class Bot(
    SelfMethods,
    MessageMethods,
    ChatMethods,
    FileMethods,
    EventMethods,
):
    """VK Teams Bot with full API coverage.

    Inherits all API method mixins and manages the polling lifecycle.

    Usage::

        async with Bot(token="...") as bot:
            dp = Dispatcher()

            @dp.message()
            async def echo(event, bot):
                await bot.send_text(event.chat.chat_id, event.text)

            await bot.start_polling(dp)
    """

    def __init__(
        self,
        bot_token: str,
        url: str = "https://api.internal.myteam.mail.ru",
        base_path: str = "/bot/v1",
        timeout: int = 30,
        poll_time: int = 15,
        last_event_id: int = 0,
        ssl: bool | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._session = VKTeamsSession(
            base_url=url,
            base_path=base_path,
            bot_token=bot_token,
            timeout=timeout,
            ssl=ssl,
            retry_policy=retry_policy,
        )
        self.poll_time = poll_time
        self.last_event_id = last_event_id

        self._running = False
        self._background_tasks: set[asyncio.Task] = set()
        self._on_startup_hooks: list[LifecycleHook] = []
        self._on_shutdown_hooks: list[LifecycleHook] = []

        self.depends: list = []

    # -- Context manager protocol ----------------------------------------------

    async def __aenter__(self) -> Bot:
        await self._session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Gracefully shut down: await pending tasks, then close session."""
        if self._background_tasks:
            logger.debug(
                "Awaiting %d background tasks...", len(self._background_tasks)
            )
            await asyncio.gather(
                *self._background_tasks, return_exceptions=True
            )
            self._background_tasks.clear()
        await self._session.close()

    # -- Lifecycle hooks -------------------------------------------------------

    def on_startup(self, callback: LifecycleHook) -> LifecycleHook:
        """Register a coroutine to run before polling starts.

        Can be used as a decorator::

            @bot.on_startup
            async def init(bot):
                print("Bot started!")
        """
        self._on_startup_hooks.append(callback)
        return callback

    def on_shutdown(self, callback: LifecycleHook) -> LifecycleHook:
        """Register a coroutine to run after polling stops.

        Can be used as a decorator::

            @bot.on_shutdown
            async def cleanup(bot):
                print("Bot stopped!")
        """
        self._on_shutdown_hooks.append(callback)
        return callback

    # -- Polling ---------------------------------------------------------------

    async def start_polling(self, dispatcher: Dispatcher) -> None:
        """Start the long-polling loop.

        Installs SIGINT/SIGTERM handlers for graceful shutdown.
        Runs on_startup hooks before polling and on_shutdown hooks after.
        """
        loop = asyncio.get_running_loop()

        # Install signal handlers for graceful shutdown
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._handle_signal)
        except NotImplementedError:
            logger.warning(
                "Signal handlers not supported on this platform; "
                "use Ctrl+C to stop"
            )

        # Run startup hooks
        for hook in self._on_startup_hooks:
            await hook(self)

        self._running = True
        logger.info("Bot polling started")

        try:
            await self._polling_loop(dispatcher)
        finally:
            self._running = False
            logger.info("Bot polling stopped")

            # Run shutdown hooks
            for hook in self._on_shutdown_hooks:
                try:
                    await hook(self)
                except Exception:
                    logger.exception("Error in shutdown hook")

            # Gracefully await pending tasks
            if self._background_tasks:
                logger.debug(
                    "Awaiting %d pending tasks...",
                    len(self._background_tasks),
                )
                await asyncio.gather(
                    *self._background_tasks, return_exceptions=True
                )
                self._background_tasks.clear()

    def _handle_signal(self) -> None:
        """Signal handler: first call stops polling gracefully, second forces exit."""
        if not self._running:
            logger.info("Forced shutdown")
            raise SystemExit(1)
        logger.info("Received shutdown signal, press Ctrl+C again to force exit")
        self._running = False

    async def _polling_loop(self, dispatcher: Dispatcher) -> None:
        """Core polling loop: fetch events and dispatch them."""
        backoff = 0.0
        max_backoff = 60.0
        while self._running:
            try:
                events = await self.get_events(
                    last_event_id=self.last_event_id,
                    poll_time=self.poll_time,
                )
                backoff = 0.0

                for event in events:
                    self._update_last_event_id(event)
                    task = asyncio.create_task(
                        self._safe_dispatch(dispatcher, event)
                    )
                    self._background_tasks.add(task)
                    task.add_done_callback(self._task_done)

            except Exception as exc:
                if not self._running:
                    break
                backoff = min(max(backoff * 2, 1.0), max_backoff)
                logger.error(
                    "Polling error (retry in %.1fs): %s",
                    backoff,
                    exc,
                    exc_info=True,
                )
                await asyncio.sleep(backoff)

    def _update_last_event_id(
        self, event: BaseEvent | RawUnknownEvent
    ) -> None:
        """Track the last event ID for long-polling offset."""
        self.last_event_id = event.event_id

    def _task_done(self, task: asyncio.Task) -> None:
        """Callback for completed dispatch tasks."""
        self._background_tasks.discard(task)
        if not task.cancelled() and task.exception():
            logger.error(
                "Unhandled exception in event handler",
                exc_info=task.exception(),
            )

    async def _safe_dispatch(
        self,
        dispatcher: Dispatcher,
        event: BaseEvent | RawUnknownEvent,
    ) -> None:
        """Dispatch a single event, catching exceptions."""
        logger.debug("Dispatching event %s: %r", event.event_id, event)
        try:
            await dispatcher.feed_event(event, self)
        except Exception:
            logger.exception("Error dispatching event %s", event.event_id)
