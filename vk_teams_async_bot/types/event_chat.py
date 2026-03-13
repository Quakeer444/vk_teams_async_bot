from __future__ import annotations

from pydantic import Field

from .base import VKTeamsFlexModel
from .enums import ChatType


class EventChatRef(VKTeamsFlexModel):
    """Lightweight chat reference carried by events.

    NOT the same shape as /chats/getInfo response.
    Events only carry chatId, type, and title.
    """

    chat_id: str = Field(alias="chatId")
    type: ChatType
    title: str | None = None
