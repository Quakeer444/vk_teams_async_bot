from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from .base import VKTeamsModel
from .enums import ChatType
from .user import PhotoUrl


class ChatInfoPrivate(VKTeamsModel):
    type: Literal[ChatType.PRIVATE] = ChatType.PRIVATE
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    nick: str | None = None
    about: str | None = None
    is_bot: bool | None = Field(default=None, alias="isBot")
    language: str | None = None
    photo: list[PhotoUrl] | None = None


class ChatInfoGroup(VKTeamsModel):
    type: Literal[ChatType.GROUP] = ChatType.GROUP
    title: str | None = None
    about: str | None = None
    rules: str | None = None
    invite_link: str | None = Field(default=None, alias="inviteLink")
    public: bool | None = None
    join_moderation: bool | None = Field(default=None, alias="joinModeration")


class ChatInfoChannel(VKTeamsModel):
    type: Literal[ChatType.CHANNEL] = ChatType.CHANNEL
    title: str | None = None
    about: str | None = None
    rules: str | None = None
    invite_link: str | None = Field(default=None, alias="inviteLink")
    public: bool | None = None
    join_moderation: bool | None = Field(default=None, alias="joinModeration")


ChatInfoResponse = Annotated[
    Union[ChatInfoPrivate, ChatInfoGroup, ChatInfoChannel],
    Field(discriminator="type"),
]
