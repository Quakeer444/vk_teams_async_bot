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
