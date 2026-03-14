"""Middleware that auto-clears expired FSM sessions."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Awaitable

from ..fsm.context import FSMContext
from ..fsm.storage.base import BaseStorage, StorageKey
from .base import BaseMiddleware, Event, HandlerType

logger = logging.getLogger(__name__)

TimeoutCallback = Callable[[str, str], Awaitable[None]]


class SessionTimeoutMiddleware(BaseMiddleware):
    """Periodically checks and clears expired FSM sessions.

    Starts a background task on first call that runs every
    ``check_interval`` seconds, clearing sessions that have been
    idle longer than ``timeout`` seconds.

    An optional ``on_timeout`` callback is invoked with
    ``(chat_id, user_id)`` for each expired session (e.g. to send
    a "session expired" message to the user).
    """

    def __init__(
        self,
        storage: BaseStorage,
        timeout: int = 300,
        check_interval: int = 60,
        on_timeout: TimeoutCallback | None = None,
    ) -> None:
        self._storage = storage
        self._timeout = timeout
        self._check_interval = check_interval
        self._on_timeout = on_timeout
        self._timestamps: dict[StorageKey, datetime] = {}
        self._task: asyncio.Task[None] | None = None

    async def __call__(
        self,
        handler: HandlerType,
        event: Event,
        data: dict[str, Any],
    ) -> Any:
        self._ensure_checker_running()

        # Update timestamp for the current user if FSM context is available
        fsm_context: FSMContext | None = data.get("fsm_context")
        if fsm_context is not None:
            self._timestamps[fsm_context._key] = datetime.now()

        return await handler(event, data)

    def _ensure_checker_running(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._checker_loop())

    async def _checker_loop(self) -> None:
        while True:
            await asyncio.sleep(self._check_interval)
            await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        now = datetime.now()
        expired: list[StorageKey] = []

        for key, ts in list(self._timestamps.items()):
            if now - ts > timedelta(seconds=self._timeout):
                expired.append(key)

        for key in expired:
            self._timestamps.pop(key, None)
            state = await self._storage.get_state(key)
            if state is not None:
                await self._storage.clear(key)
                logger.info("Session expired for %s", key)
                if self._on_timeout:
                    chat_id, user_id = key
                    try:
                        await self._on_timeout(chat_id, user_id)
                    except Exception:
                        logger.exception(
                            "Error in timeout callback for %s", key
                        )

    async def close(self) -> None:
        """Cancel the background checker task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
