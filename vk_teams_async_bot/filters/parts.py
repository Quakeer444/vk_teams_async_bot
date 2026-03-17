"""Message part filters: file, reply, forward, voice, sticker, mention."""

from __future__ import annotations

from ..types.event import BaseEvent, NewMessageEvent
from ..types.message import (
    FilePart,
    ForwardPart,
    MentionPart,
    ReplyPart,
    StickerPart,
    VoicePart,
)
from .base import FilterBase


class FileFilter(FilterBase):
    """Match messages containing file parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, FilePart) for p in event.parts)

    def __repr__(self) -> str:
        return "FileFilter()"


class ReplyFilter(FilterBase):
    """Match messages containing reply parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, ReplyPart) for p in event.parts)

    def __repr__(self) -> str:
        return "ReplyFilter()"


class ForwardFilter(FilterBase):
    """Match messages containing forward parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, ForwardPart) for p in event.parts)

    def __repr__(self) -> str:
        return "ForwardFilter()"


class VoiceFilter(FilterBase):
    """Match messages containing voice parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, VoicePart) for p in event.parts)

    def __repr__(self) -> str:
        return "VoiceFilter()"


class StickerFilter(FilterBase):
    """Match messages containing sticker parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, StickerPart) for p in event.parts)

    def __repr__(self) -> str:
        return "StickerFilter()"


class MentionFilter(FilterBase):
    """Match messages containing mention parts."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(isinstance(p, MentionPart) for p in event.parts)

    def __repr__(self) -> str:
        return "MentionFilter()"


class FileTypeFilter(FilterBase):
    """Match messages containing file parts of a specific type.

    Checks FilePartPayload.type against the given type(s).
    Values: "image", "audio", "video".
    """

    def __init__(self, file_types: str | list[str]) -> None:
        if isinstance(file_types, str):
            self._types = frozenset([file_types])
        else:
            self._types = frozenset(file_types)

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(
            isinstance(p, FilePart) and p.payload.type in self._types
            for p in event.parts
        )

    def __repr__(self) -> str:
        return f"FileTypeFilter(types={sorted(self._types)!r})"


class MentionUserFilter(FilterBase):
    """Match messages that mention a specific user by user_id.

    Unlike MentionFilter (which checks for any mention), this filter
    checks if any MentionPart.payload.user_id matches the given ID(s).
    Uses frozenset internally for O(1) lookup.
    """

    def __init__(self, user_ids: str | list[str]) -> None:
        if isinstance(user_ids, str):
            self._user_ids = frozenset([user_ids])
        else:
            self._user_ids = frozenset(user_ids)

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        return any(
            isinstance(p, MentionPart) and p.payload.user_id in self._user_ids
            for p in event.parts
        )

    def __repr__(self) -> str:
        return f"MentionUserFilter(user_ids={sorted(self._user_ids)!r})"
