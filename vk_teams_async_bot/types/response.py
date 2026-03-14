from __future__ import annotations

from pydantic import Field

from .base import VKTeamsModel
from .user import UserAdmin


class OkResponse(VKTeamsModel):
    ok: bool


class OkWithDescriptionResponse(VKTeamsModel):
    ok: bool
    description: str | None = None


class MessageResponse(VKTeamsModel):
    ok: bool
    msg_id: str = Field(alias="msgId")


class FileUploadResponse(VKTeamsModel):
    ok: bool
    file_id: str = Field(alias="fileId")
    msg_id: str = Field(alias="msgId")


class ChatCreateResponse(VKTeamsModel):
    ok: bool = True
    sn: str


class MemberFailure(VKTeamsModel):
    id: str
    error: str


class PartialSuccessResponse(VKTeamsModel):
    ok: bool
    failures: list[MemberFailure] | None = None


class MembersResponse(VKTeamsModel):
    ok: bool = True
    members: list[UserAdmin]
    cursor: str | None = None


class AdminsResponse(VKTeamsModel):
    ok: bool = True
    admins: list[UserAdmin]


class UserIdItem(VKTeamsModel):
    user_id: str = Field(alias="userId")


class UsersResponse(VKTeamsModel):
    ok: bool = True
    users: list[UserIdItem]


class ErrorResponse(VKTeamsModel):
    ok: bool
    description: str
