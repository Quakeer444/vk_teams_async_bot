from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from .base import VKTeamsResponseModel
from .enums import ChatType
from .user import PhotoUrl


class ChatInfoPrivate(VKTeamsResponseModel):
    ok: bool = True
    type: Literal[ChatType.PRIVATE] = ChatType.PRIVATE
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    nick: str | None = None
    about: str | None = None
    is_bot: bool | None = Field(default=None, alias="isBot")
    language: str | None = None
    photo: list[PhotoUrl] | None = None


class _ChatInfoGroupLike(VKTeamsResponseModel):
    """Shared fields for group and channel chat info."""

    ok: bool = True
    title: str | None = None
    about: str | None = None
    rules: str | None = None
    invite_link: str | None = Field(default=None, alias="inviteLink")
    public: bool | None = None
    join_moderation: bool | None = Field(default=None, alias="joinModeration")


class ChatInfoGroup(_ChatInfoGroupLike):
    type: Literal[ChatType.GROUP] = ChatType.GROUP


class ChatInfoChannel(_ChatInfoGroupLike):
    type: Literal[ChatType.CHANNEL] = ChatType.CHANNEL


ChatInfoResponse = Annotated[
    Union[ChatInfoPrivate, ChatInfoGroup, ChatInfoChannel],
    Field(discriminator="type"),
]
