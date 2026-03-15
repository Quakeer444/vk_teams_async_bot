"""Shared utility functions for the VK Teams async bot."""

from __future__ import annotations

from .types.event import (
    BaseEvent,
    CallbackQueryEvent,
    EditedMessageEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    RawUnknownEvent,
)


def extract_chat_user(
    event: BaseEvent | RawUnknownEvent,
) -> tuple[str, str] | None:
    """Extract (chat_id, user_id) from an event for FSM context.

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
