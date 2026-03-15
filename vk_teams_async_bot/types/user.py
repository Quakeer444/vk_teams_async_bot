from __future__ import annotations

from pydantic import Field

from .base import VKTeamsFlexModel, VKTeamsResponseModel


class PhotoUrl(VKTeamsResponseModel):
    url: str


class User(VKTeamsFlexModel):
    user_id: str = Field(alias="userId")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    nick: str | None = None


class BotInfo(VKTeamsResponseModel):
    user_id: str = Field(alias="userId")
    nick: str | None = None
    first_name: str | None = Field(default=None, alias="firstName")
    about: str | None = None
    photo: list[PhotoUrl] | None = None


class UserAdmin(VKTeamsResponseModel):
    user_id: str = Field(alias="userId")
    creator: bool | None = None
    admin: bool | None = None
