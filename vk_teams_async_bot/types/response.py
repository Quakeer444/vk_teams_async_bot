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
    sn: str


class MemberFailure(VKTeamsModel):
    id: str
    error: str


class PartialSuccessResponse(VKTeamsModel):
    ok: bool
    failures: list[MemberFailure] | None = None


class MembersResponse(VKTeamsModel):
    members: list[UserAdmin]
    cursor: str | None = None


class AdminsResponse(VKTeamsModel):
    admins: list[UserAdmin]


class UserIdItem(VKTeamsModel):
    user_id: str = Field(alias="userId")


class UsersResponse(VKTeamsModel):
    users: list[UserIdItem]


class ErrorResponse(VKTeamsModel):
    ok: bool
    description: str
