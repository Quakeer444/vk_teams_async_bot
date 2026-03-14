"""Typed models for VK Teams Bot API events."""

from __future__ import annotations

import logging
from typing import Annotated, Literal, Union

from pydantic import Field, ValidationError, model_validator

from ..errors import EventParsingError
from .base import VKTeamsFlexModel
from .enums import EventType
from .event_chat import EventChatRef
from .message import MessagePart, NestedMessage, parse_parts
from .user import User

logger = logging.getLogger(__name__)


class BaseEvent(VKTeamsFlexModel):
    """Base for all known event types."""

    event_id: int = Field(alias="eventId")
    type: EventType


class NewMessageEvent(BaseEvent):
    """A new message was received."""

    type: Literal[EventType.NEW_MESSAGE] = EventType.NEW_MESSAGE
    chat: EventChatRef
    from_: User = Field(alias="from")
    msg_id: str = Field(alias="msgId")
    text: str | None = None
    format_: dict | None = Field(default=None, alias="format")
    timestamp: int | None = None
    parts: list[MessagePart] | None = None

    @model_validator(mode="before")
    @classmethod
    def _parse_raw_parts(cls, data: dict) -> dict:
        """Convert raw parts dicts to typed MessagePart objects."""
        if isinstance(data, dict) and "parts" in data:
            raw = data["parts"]
            if isinstance(raw, list) and raw and isinstance(raw[0], dict):
                data = {**data, "parts": parse_parts(raw)}
        return data


class EditedMessageEvent(BaseEvent):
    """A message was edited."""

    type: Literal[EventType.EDITED_MESSAGE] = EventType.EDITED_MESSAGE
    chat: EventChatRef
    from_: User = Field(alias="from")
    msg_id: str = Field(alias="msgId")
    text: str | None = None
    format_: dict | None = Field(default=None, alias="format")
    timestamp: int | None = None
    edited_timestamp: int | None = Field(default=None, alias="editedTimestamp")


class DeletedMessageEvent(BaseEvent):
    """A message was deleted."""

    type: Literal[EventType.DELETED_MESSAGE] = EventType.DELETED_MESSAGE
    chat: EventChatRef
    msg_id: str = Field(alias="msgId")
    timestamp: int | None = None


class PinnedMessageEvent(BaseEvent):
    """A message was pinned."""

    type: Literal[EventType.PINNED_MESSAGE] = EventType.PINNED_MESSAGE
    chat: EventChatRef
    from_: User = Field(alias="from")
    msg_id: str = Field(alias="msgId")
    text: str | None = None
    timestamp: int | None = None


class UnpinnedMessageEvent(BaseEvent):
    """A message was unpinned."""

    type: Literal[EventType.UNPINNED_MESSAGE] = EventType.UNPINNED_MESSAGE
    chat: EventChatRef
    msg_id: str = Field(alias="msgId")
    timestamp: int | None = None


class NewChatMembersEvent(BaseEvent):
    """New members joined or were added to a chat."""

    type: Literal[EventType.NEW_CHAT_MEMBERS] = EventType.NEW_CHAT_MEMBERS
    chat: EventChatRef
    new_members: list[User] = Field(alias="newMembers")
    added_by: User = Field(alias="addedBy")


class LeftChatMembersEvent(BaseEvent):
    """Members left or were removed from a chat."""

    type: Literal[EventType.LEFT_CHAT_MEMBERS] = EventType.LEFT_CHAT_MEMBERS
    chat: EventChatRef
    left_members: list[User] = Field(alias="leftMembers")
    removed_by: User = Field(alias="removedBy")


class CallbackQueryEvent(BaseEvent):
    """A callback button was pressed."""

    type: Literal[EventType.CALLBACK_QUERY] = EventType.CALLBACK_QUERY
    chat: EventChatRef
    from_: User = Field(alias="from")
    query_id: str = Field(alias="queryId")
    callback_data: str = Field(alias="callbackData")
    message: NestedMessage | None = None


class RawUnknownEvent(VKTeamsFlexModel):
    """Fallback for undocumented or unknown event types."""

    event_id: int = Field(alias="eventId")
    type: str
    payload: dict


Event = Annotated[
    Union[
        NewMessageEvent,
        EditedMessageEvent,
        DeletedMessageEvent,
        PinnedMessageEvent,
        UnpinnedMessageEvent,
        NewChatMembersEvent,
        LeftChatMembersEvent,
        CallbackQueryEvent,
    ],
    Field(discriminator="type"),
]


def _flatten_raw_event(raw: dict) -> dict:
    """Flatten {eventId, type, payload: {...}} into a single dict."""
    payload = raw.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    return {
        "eventId": raw["eventId"],
        "type": raw["type"],
        **payload,
    }


def parse_event(raw: dict) -> BaseEvent | RawUnknownEvent:
    """Parse a raw event dict into a typed event model.

    Known event types are parsed via the discriminated Event union.
    Unknown types produce a RawUnknownEvent (never raise).
    Malformed payloads (missing required fields) raise EventParsingError
    with the raw data attached.
    """
    from pydantic import TypeAdapter

    event_type = raw.get("type")

    # Check if event type is known
    known_types = {member.value for member in EventType}
    if event_type not in known_types:
        logger.warning("Unknown event type: %s", event_type)
        return RawUnknownEvent(
            eventId=raw.get("eventId", 0),
            type=event_type or "",
            payload=raw.get("payload", {}),
        )

    # Flatten the raw event structure
    try:
        flat = _flatten_raw_event(raw)
    except (KeyError, TypeError) as exc:
        raise EventParsingError(
            f"Failed to flatten event: {exc}",
            raw_data=raw,
        ) from exc

    # Parse via discriminated union
    adapter = TypeAdapter(Event)
    try:
        return adapter.validate_python(flat)
    except ValidationError as exc:
        raise EventParsingError(
            f"Failed to parse event type={event_type}: {exc}",
            raw_data=raw,
        ) from exc
