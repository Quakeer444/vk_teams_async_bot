from __future__ import annotations

from pydantic import Field

from .base import VKTeamsResponseModel
from .user import ThreadSubscriber, UserAdmin


class OkResponse(VKTeamsResponseModel):
    ok: bool


class OkWithDescriptionResponse(VKTeamsResponseModel):
    ok: bool
    description: str | None = None


class MessageResponse(VKTeamsResponseModel):
    ok: bool
    msg_id: str = Field(alias="msgId")


class FileUploadResponse(VKTeamsResponseModel):
    ok: bool
    file_id: str = Field(alias="fileId")
    msg_id: str = Field(alias="msgId")


class ChatCreateResponse(VKTeamsResponseModel):
    ok: bool = True
    sn: str


class MemberFailure(VKTeamsResponseModel):
    id: str
    error: str


class PartialSuccessResponse(VKTeamsResponseModel):
    ok: bool
    failures: list[MemberFailure] | None = None


class MembersResponse(VKTeamsResponseModel):
    ok: bool = True
    members: list[UserAdmin]
    cursor: str | None = None


class AdminsResponse(VKTeamsResponseModel):
    ok: bool = True
    admins: list[UserAdmin]


class UserIdItem(VKTeamsResponseModel):
    user_id: str = Field(alias="userId")


class UsersResponse(VKTeamsResponseModel):
    ok: bool = True
    users: list[UserIdItem]


class ErrorResponse(VKTeamsResponseModel):
    ok: bool
    description: str


class ThreadResponse(VKTeamsResponseModel):
    ok: bool = True
    thread_id: str = Field(alias="threadId")


class ThreadSubscribersResponse(VKTeamsResponseModel):
    ok: bool = True
    subscribers: list[ThreadSubscriber]
    cursor: str | None = None
