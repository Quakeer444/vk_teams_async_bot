"""FSM state filter for matching current user state."""

from __future__ import annotations

from ..fsm.context import FSMContext
from ..fsm.state import State
from ..fsm.storage.base import BaseStorage
from ..types.event import BaseEvent
from ..utils import extract_chat_user
from .base import FilterBase


class StateFilter(FilterBase):
    """Match the current FSM state for a user in a chat.

    This filter is inherently async because it needs storage access.
    The synchronous __call__ raises NotImplementedError -- the handler
    system (dispatcher) should call the async check() method instead.
    """

    def __init__(self, state: State | str, storage: BaseStorage | None = None) -> None:
        self._state = state
        self._storage = storage

    @property
    def target_state(self) -> str | None:
        """Return the target state string for comparison."""
        if isinstance(self._state, State):
            return self._state.state
        return self._state

    async def check(self, event: BaseEvent) -> bool:
        """Async check: compare the user's current FSM state with the target."""
        if self._storage is None:
            return False
        key = extract_chat_user(event)
        if key is None:
            return False
        ctx = FSMContext(storage=self._storage, key=key)
        current = await ctx.get_state()
        return current == self.target_state

    async def check_async(self, event: BaseEvent) -> bool:
        """Override base class to use async storage lookup."""
        return await self.check(event)

    def set_storage(self, storage: BaseStorage) -> None:
        """Set the storage backend for state lookups."""
        self._storage = storage

    def __call__(self, event: BaseEvent) -> bool:
        raise NotImplementedError(
            "StateFilter requires async check(). "
            "Use the handler's async filter support."
        )

    def __repr__(self) -> str:
        return f"StateFilter(state={self.target_state!r})"
