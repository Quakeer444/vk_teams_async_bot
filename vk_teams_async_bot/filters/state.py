"""FSM state filters for matching current user state."""

from __future__ import annotations

from ..fsm.context import FSMContext
from ..fsm.state import State, StatesGroup
from ..fsm.storage.base import BaseStorage
from ..types.event import BaseEvent
from ..utils import extract_chat_user
from .base import FilterBase


class StateFilter(FilterBase):
    """Match the current FSM state for a user in a chat.

    Supports three modes:
    - ``StateFilter(State(...))`` or ``StateFilter("GroupName:state")`` -- exact match
    - ``StateFilter("*")`` or ``StateFilter(State("*"))`` -- any non-null state
    - ``StateFilter(None)`` -- user has no state (initial/cleared)

    This filter is inherently async because it needs storage access.
    The synchronous __call__ raises NotImplementedError -- the handler
    system (dispatcher) should call the async check() method instead.
    """

    def __init__(
        self, state: State | str | None, storage: BaseStorage | None = None
    ) -> None:
        self._state = state
        self._storage = storage

    @property
    def target_state(self) -> str | None:
        """Return the target state string for comparison."""
        if self._state is None:
            return None
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
        target = self.target_state
        if target == "*":
            return current is not None
        if target is None:
            return current is None
        return current == target

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


class StatesGroupFilter(FilterBase):
    """Match any state within a StatesGroup."""

    def __init__(
        self, group: type[StatesGroup], storage: BaseStorage | None = None
    ) -> None:
        self._group = group
        self._state_names = frozenset(group.all_state_names())
        self._storage = storage

    async def check(self, event: BaseEvent) -> bool:
        if self._storage is None:
            return False
        key = extract_chat_user(event)
        if key is None:
            return False
        ctx = FSMContext(storage=self._storage, key=key)
        current = await ctx.get_state()
        return current in self._state_names

    async def check_async(self, event: BaseEvent) -> bool:
        return await self.check(event)

    def set_storage(self, storage: BaseStorage) -> None:
        """Set the storage backend for state lookups."""
        self._storage = storage

    def __call__(self, event: BaseEvent) -> bool:
        raise NotImplementedError("StatesGroupFilter requires async check().")

    def __repr__(self) -> str:
        return f"StatesGroupFilter(group={self._group.__name__!r})"
