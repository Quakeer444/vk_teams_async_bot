"""In-memory storage backend for FSM."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseStorage, StorageKey

logger = logging.getLogger(__name__)


class MemoryStorage(BaseStorage):
    """In-memory storage implementation.

    Suitable for development and single-process deployments.
    All data is lost when the process exits.
    """

    def __init__(self) -> None:
        self._states: dict[StorageKey, str | None] = {}
        self._data: dict[StorageKey, dict[str, Any]] = {}

    async def get_state(self, key: StorageKey) -> str | None:
        return self._states.get(key)

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        logger.debug("MemoryStorage.set_state: key=%s, state=%s", key, state)
        if state is None:
            self._states.pop(key, None)
        else:
            self._states[key] = state

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        return self._data.get(key, {}).copy()

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        self._data[key] = data.copy()

    async def update_data(
        self, key: StorageKey, data: dict[str, Any]
    ) -> dict[str, Any]:
        current = self._data.get(key, {})
        updated = {**current, **data}
        self._data[key] = updated
        return updated.copy()

    async def clear(self, key: StorageKey) -> None:
        logger.debug("MemoryStorage.clear: key=%s", key)
        self._states.pop(key, None)
        self._data.pop(key, None)

    async def close(self) -> None:
        logger.debug(
            "MemoryStorage closed (%d states, %d data entries)",
            len(self._states),
            len(self._data),
        )
        self._states.clear()
        self._data.clear()
