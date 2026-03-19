"""Typed models for message parts (file, sticker, mention, voice, forward, reply)."""

from __future__ import annotations

import logging
from typing import Annotated, Literal, Union

from pydantic import Field, TypeAdapter, ValidationError, model_validator

from .base import VKTeamsFlexModel
from .enums import Parts
from .user import User

logger = logging.getLogger(__name__)


class NestedMessageChat(VKTeamsFlexModel):
    """Chat reference inside a nested message (callbackQuery, forward, reply)."""

    chat_id: str = Field(alias="chatId")
    type: str | None = None
    title: str | None = None


class NestedMessage(VKTeamsFlexModel):
    """Shared model for forward/reply/callbackQuery message payloads.

    The VK Teams API wraps callbackQuery messages in the full event
    structure: ``{eventId, type, payload: {msgId, chat, from, ...}}``.
    The model validator flattens this so fields are accessible directly.
    """

    from_: User = Field(alias="from")
    msg_id: str = Field(alias="msgId")
    text: str | None = None
    format_: dict | None = Field(default=None, alias="format")
    timestamp: int | None = None
    chat: NestedMessageChat | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten_nested_payload(cls, data: dict) -> dict:
        """Flatten {eventId, type, payload: {...}} into a single dict."""
        if (
            isinstance(data, dict)
            and "payload" in data
            and isinstance(data["payload"], dict)
        ):
            payload = data["payload"]
            return {**data, **payload}
        return data


class FilePartPayload(VKTeamsFlexModel):
    """Payload for file and voice parts."""

    file_id: str = Field(alias="fileId")
    caption: str | None = None
    type: str | None = None
    format_: dict | None = Field(default=None, alias="format")


class StickerPartPayload(VKTeamsFlexModel):
    """Payload for sticker parts."""

    file_id: str = Field(alias="fileId")


class ForwardPartPayload(VKTeamsFlexModel):
    """Payload for forward parts."""

    message: NestedMessage


class ReplyPartPayload(VKTeamsFlexModel):
    """Payload for reply parts."""

    message: NestedMessage


class FilePart(VKTeamsFlexModel):
    """A file attachment in a message."""

    type: Literal[Parts.FILE] = Parts.FILE
    payload: FilePartPayload


class StickerPart(VKTeamsFlexModel):
    """A sticker in a message."""

    type: Literal[Parts.STICKER] = Parts.STICKER
    payload: StickerPartPayload


class MentionPart(VKTeamsFlexModel):
    """A user mention in a message."""

    type: Literal[Parts.MENTION] = Parts.MENTION
    payload: User


class VoicePart(VKTeamsFlexModel):
    """A voice message."""

    type: Literal[Parts.VOICE] = Parts.VOICE
    payload: FilePartPayload


class ForwardPart(VKTeamsFlexModel):
    """A forwarded message."""

    type: Literal[Parts.FORWARD] = Parts.FORWARD
    payload: ForwardPartPayload


class ReplyPart(VKTeamsFlexModel):
    """A reply to a message."""

    type: Literal[Parts.REPLY] = Parts.REPLY
    payload: ReplyPartPayload


MessagePart = Annotated[
    Union[FilePart, StickerPart, MentionPart, VoicePart, ForwardPart, ReplyPart],
    Field(discriminator="type"),
]

_part_adapter: TypeAdapter[MessagePart] = TypeAdapter(MessagePart)


def parse_parts(raw_parts: list[dict]) -> list[MessagePart]:
    """Parse message parts, skipping unknown types with a warning.

    For each raw part dict, attempts to validate it as a MessagePart
    via the discriminated union. Unknown or malformed parts are logged
    and skipped -- they never raise.
    """
    result: list[MessagePart] = []

    for raw in raw_parts:
        part_type = raw.get("type", "<missing>")
        try:
            parsed = _part_adapter.validate_python(raw)
            result.append(parsed)
        except ValidationError:
            logger.warning(
                "Skipping unknown or malformed message part type=%s",
                part_type,
            )

    return result
