"""Abstract base class for FSM storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

StorageKey = tuple[str, str]  # (chat_id, user_id)


class BaseStorage(ABC):
    """Abstract storage interface for FSM state and data.

    All implementations must key data on (chat_id, user_id) tuples,
    allowing the same user to have independent state in different chats.
    """

    @abstractmethod
    async def get_state(self, key: StorageKey) -> str | None:
        """Return current state for the given key, or None if not set."""
        ...

    @abstractmethod
    async def set_state(self, key: StorageKey, state: str | None) -> None:
        """Set the state for the given key. Pass None to clear."""
        ...

    @abstractmethod
    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        """Return a copy of stored data for the given key."""
        ...

    @abstractmethod
    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        """Replace all stored data for the given key."""
        ...

    @abstractmethod
    async def update_data(
        self, key: StorageKey, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge data into existing data and return the updated copy."""
        ...

    @abstractmethod
    async def clear(self, key: StorageKey) -> None:
        """Clear both state and data for the given key."""
        ...

    async def close(self) -> None:
        """Release resources. Override in subclasses that need cleanup."""
