"""FSM context -- per-user facade over storage operations."""

from __future__ import annotations

import logging
from typing import Any

from .state import State
from .storage.base import BaseStorage, StorageKey

logger = logging.getLogger(__name__)


class FSMContext:
    """Per-user state and data operations.

    Wraps a storage backend with a fixed (chat_id, user_id) key,
    intended to be injected into handlers as a dependency.
    """

    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self._storage = storage
        self._key = key

    async def get_state(self) -> str | None:
        """Return the current state string, or None."""
        return await self._storage.get_state(self._key)

    async def set_state(self, state: State | str | None) -> None:
        """Set the current state.

        Accepts a State object (uses its .state property),
        a raw string, or None to clear.
        """
        if isinstance(state, State):
            raw = state.state
        else:
            raw = state
        logger.debug("FSM state transition: key=%s, new_state=%s", self._key, raw)
        await self._storage.set_state(self._key, raw)

    async def get_data(self) -> dict[str, Any]:
        """Return a copy of the stored data dict."""
        return await self._storage.get_data(self._key)

    async def set_data(self, data: dict[str, Any]) -> None:
        """Replace all stored data."""
        logger.debug("FSM data replaced: key=%s", self._key)
        await self._storage.set_data(self._key, data)

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        """Merge kwargs into existing data and return the result."""
        logger.debug(
            "FSM data updated: key=%s, keys=%s", self._key, list(kwargs.keys())
        )
        return await self._storage.update_data(self._key, data=kwargs)

    async def clear(self) -> None:
        """Clear both state and data."""
        logger.debug("FSM state cleared: key=%s", self._key)
        await self._storage.clear(self._key)
