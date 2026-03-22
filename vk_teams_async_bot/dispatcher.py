"""Event dispatcher with middleware chain, handler routing, and decorator shortcuts."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Sequence

from .filters.base import FilterBase
from .filters.message import CommandFilter
from .filters.state import StateFilter
from .fsm.context import FSMContext
from .fsm.storage.base import BaseStorage
from .handlers.base import BaseHandler
from .handlers.callback_query import CallbackQueryHandler
from .handlers.chat_member import LeftChatMembersHandler, NewChatMembersHandler
from .handlers.command import CommandHandler
from .handlers.deleted_message import DeletedMessageHandler
from .handlers.edited_message import EditedMessageHandler
from .handlers.message import MessageHandler
from .handlers.pinned_message import PinnedMessageHandler, UnpinnedMessageHandler
from .middleware.base import BaseMiddleware
from .middleware.manager import MiddlewareManager
from .types.event import BaseEvent, RawUnknownEvent
from .utils import extract_chat_user

if TYPE_CHECKING:
    from .bot import Bot

logger = logging.getLogger(__name__)


class Dispatcher:
    """Routes events through middleware chain to matching handlers.

    Supports decorator shortcuts for registering handlers::

        dp = Dispatcher()

        @dp.message(CommandFilter("/start"))
        async def on_start(event, bot):
            await bot.send_text(event.chat.chat_id, "Hello!")

        @dp.callback_query()
        async def on_button(event, bot):
            await bot.answer_callback_query(event.query_id)
    """

    def __init__(
        self,
        storage: BaseStorage | None = None,
        lock_sweep_interval: float = 60.0,
    ) -> None:
        self.handlers: list[BaseHandler] = []
        self.middleware = MiddlewareManager()
        self._storage = storage
        self._user_locks: dict[tuple[str, str], asyncio.Lock] = {}
        self._lock_sweep_interval = lock_sweep_interval
        self._sweep_task: asyncio.Task[None] | None = None
        logger.debug(
            "Dispatcher created (storage=%s, sweep_interval=%.1fs)",
            type(storage).__name__ if storage else None,
            lock_sweep_interval,
        )

    def add_middleware(self, mw: BaseMiddleware) -> None:
        """Register a middleware instance."""
        logger.debug("Middleware registered: %s", type(mw).__name__)
        self.middleware.add(mw)

    def add_handler(self, handler: BaseHandler) -> None:
        """Register a handler instance."""
        logger.debug("Handler registered: %s", type(handler).__name__)
        self.handlers.append(handler)

    # -- Decorator shortcuts ---------------------------------------------------

    def _register(
        self,
        handler_cls: type[BaseHandler],
        filters: tuple[FilterBase, ...],
    ) -> Callable:
        """Create a decorator that registers a handler of *handler_cls*."""

        def decorator(callback: Callable) -> Callable:
            handler = handler_cls(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def message(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``MessageHandler``."""
        return self._register(MessageHandler, filters)

    def edited_message(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``EditedMessageHandler``."""
        return self._register(EditedMessageHandler, filters)

    def deleted_message(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``DeletedMessageHandler``."""
        return self._register(DeletedMessageHandler, filters)

    def pinned_message(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``PinnedMessageHandler``."""
        return self._register(PinnedMessageHandler, filters)

    def unpinned_message(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``UnpinnedMessageHandler``."""
        return self._register(UnpinnedMessageHandler, filters)

    def new_chat_members(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``NewChatMembersHandler``."""
        return self._register(NewChatMembersHandler, filters)

    def left_chat_members(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``LeftChatMembersHandler``."""
        return self._register(LeftChatMembersHandler, filters)

    def callback_query(self, *filters: FilterBase) -> Callable:
        """Decorator shortcut for ``CallbackQueryHandler``."""
        return self._register(CallbackQueryHandler, filters)

    def command(
        self,
        cmd: str,
        *filters: FilterBase,
    ) -> Callable:
        """Convenience decorator for command handlers.

        Equivalent to ``@dp.message(CommandFilter(cmd), *filters)``::

            @dp.command("start")
            async def on_start(event, bot):
                await bot.send_text(event.chat.chat_id, "Hello!")
        """
        return self.message(CommandFilter(cmd), *filters)

    # -- Event processing ------------------------------------------------------

    async def feed_event(self, event: BaseEvent | RawUnknownEvent, bot: Bot) -> None:
        """Process a single event through the middleware chain and handlers.

        This is the main entry point called by Bot.start_polling().
        """
        if isinstance(event, RawUnknownEvent):
            logger.warning("Skipping unknown event type: %s", event.type)
            return

        data: dict[str, Any] = {
            "bot": bot,
            "dispatcher": self,
        }

        # Inject FSMContext if storage is configured
        user_key = None
        if self._storage is not None:
            user_key = extract_chat_user(event)
            if user_key is not None:
                data["fsm_context"] = FSMContext(storage=self._storage, key=user_key)
                logger.debug("FSMContext injected for key=%s", user_key)

        # Build the handler chain wrapped by middlewares
        wrapped = self.middleware.wrap(self._dispatch_to_handler)
        if user_key is not None:
            lock = self._user_locks.setdefault(user_key, asyncio.Lock())
            async with lock:
                await wrapped(event, data)
        else:
            await wrapped(event, data)

    async def _dispatch_to_handler(
        self,
        event: BaseEvent | RawUnknownEvent,
        data: dict[str, Any],
    ) -> None:
        """Find the first matching handler and execute it."""
        if not isinstance(event, BaseEvent):
            logger.debug("Skipping non-BaseEvent in dispatch: %s", type(event).__name__)
            return
        bot = data["bot"]

        for handler in self.handlers:
            # Use async check if handler has async filters (e.g. StateFilter)
            if handler.has_async_filters():
                # Inject storage into StateFilter if needed
                if self._storage is not None:
                    self._inject_storage(handler)
                if not await handler.check_async(event):
                    continue
            else:
                if not handler.check(event):
                    continue

            await handler.handle(event, bot, extra_kwargs=data)
            logger.debug(
                "Handler matched: %s for event %s",
                type(handler).__name__,
                event.event_id,
            )
            return
        logger.debug(
            "No handler matched for event %s (type=%s)",
            event.event_id,
            type(event).__name__,
        )

    def start_sweep_task(self) -> None:
        """Start the periodic lock sweep background task."""
        if self._sweep_task is None or self._sweep_task.done():
            self._sweep_task = asyncio.create_task(self._sweep_loop())
            logger.debug(
                "Lock sweep task started (interval=%.1fs)",
                self._lock_sweep_interval,
            )

    async def _sweep_loop(self) -> None:
        """Periodically sweep idle user locks."""
        while True:
            await asyncio.sleep(self._lock_sweep_interval)
            try:
                self._sweep_idle_locks()
            except Exception:
                logger.exception("Error during lock sweep")

    async def stop_sweep_task(self) -> None:
        """Cancel the periodic lock sweep background task."""
        if self._sweep_task and not self._sweep_task.done():
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass
            logger.debug("Lock sweep task stopped")

    def _sweep_idle_locks(self) -> None:
        """Remove user locks not currently held and without pending waiters.

        Safe to call periodically: coroutines already holding a lock
        reference continue to work even after the key is removed from
        the dict.
        """
        idle_keys = [
            k
            for k, v in self._user_locks.items()
            if not v.locked() and not getattr(v, "_waiters", [])
        ]
        for k in idle_keys:
            del self._user_locks[k]

    def _inject_storage(self, handler: BaseHandler) -> None:
        """Ensure StateFilter instances have a reference to the storage."""
        if self._storage is None or not handler.filters:
            return

        filters: Sequence[FilterBase]
        if isinstance(handler.filters, FilterBase):
            filters = [handler.filters]
        else:
            filters = handler.filters

        for f in filters:
            for leaf in f.iter_filters():
                if isinstance(leaf, StateFilter) and leaf._storage is None:
                    leaf.set_storage(self._storage)
