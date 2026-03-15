"""FSM state filter for matching current user state."""

from __future__ import annotations

from ..fsm.context import FSMContext
from ..fsm.state import State
from ..fsm.storage.base import BaseStorage
from ..types.event import (
    BaseEvent,
    CallbackQueryEvent,
    EditedMessageEvent,
    NewMessageEvent,
    PinnedMessageEvent,
)
from .base import FilterBase


def _extract_chat_user(event: BaseEvent) -> tuple[str, str] | None:
    """Extract (chat_id, user_id) from an event, or None if not possible.

    Supports events that carry both a chat reference and a from_ user:
    NewMessageEvent, EditedMessageEvent, CallbackQueryEvent, PinnedMessageEvent.
    """
    if isinstance(event, (NewMessageEvent, EditedMessageEvent, PinnedMessageEvent)):
        return event.chat.chat_id, event.from_.user_id
    if isinstance(event, CallbackQueryEvent):
        if event.chat is None:
            return None
        return event.chat.chat_id, event.from_.user_id
    return None


class StateFilter(FilterBase):
    """Match the current FSM state for a user in a chat.

    This filter is inherently async because it needs storage access.
    The synchronous __call__ raises NotImplementedError -- the handler
    system (dispatcher) should call the async check() method instead.
    """

    def __init__(self, state: State | str, storage: BaseStorage) -> None:
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
        key = _extract_chat_user(event)
        if key is None:
            return False
        ctx = FSMContext(storage=self._storage, key=key)
        current = await ctx.get_state()
        return current == self.target_state

    def __call__(self, event: BaseEvent) -> bool:
        raise NotImplementedError(
            "StateFilter requires async check(). "
            "Use the handler's async filter support."
        )

    def __repr__(self) -> str:
        return f"StateFilter(state={self.target_state!r})"
