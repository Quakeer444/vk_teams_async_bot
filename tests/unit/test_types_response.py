import pytest
from pydantic import ValidationError

from vk_teams_async_bot.types.response import (
    AdminsResponse,
    ChatCreateResponse,
    ErrorResponse,
    FileUploadResponse,
    MemberFailure,
    MembersResponse,
    MessageResponse,
    OkResponse,
    OkWithDescriptionResponse,
    PartialSuccessResponse,
    UserIdItem,
    UsersResponse,
)


class TestOkResponse:
    def test_ok_true(self):
        r = OkResponse(ok=True)
        assert r.ok is True

    def test_ok_false(self):
        r = OkResponse(ok=False)
        assert r.ok is False

    def test_extra_ignored(self):
        r = OkResponse(ok=True, extra="nope")
        assert r.ok is True

    def test_round_trip(self):
        data = {"ok": True}
        r = OkResponse(**data)
        assert r.model_dump() == data


class TestOkWithDescriptionResponse:
    def test_with_description(self):
        r = OkWithDescriptionResponse(ok=False, description="Image is porn")
        assert r.ok is False
        assert r.description == "Image is porn"

    def test_without_description(self):
        r = OkWithDescriptionResponse(ok=True)
        assert r.description is None


class TestMessageResponse:
    def test_from_dict(self):
        r = MessageResponse(ok=True, msgId="12345")
        assert r.msg_id == "12345"

    def test_round_trip(self):
        data = {"ok": True, "msgId": "99"}
        r = MessageResponse(**data)
        dumped = r.model_dump(by_alias=True)
        assert dumped == data


class TestFileUploadResponse:
    def test_from_dict(self):
        r = FileUploadResponse(ok=True, fileId="f123", msgId="m456")
        assert r.file_id == "f123"
        assert r.msg_id == "m456"


class TestChatCreateResponse:
    def test_from_dict(self):
        r = ChatCreateResponse(sn="chat123@chat.agent")
        assert r.sn == "chat123@chat.agent"


class TestPartialSuccessResponse:
    def test_full_success(self):
        r = PartialSuccessResponse(ok=True)
        assert r.failures is None

    def test_with_failures(self):
        r = PartialSuccessResponse(
            ok=True,
            failures=[
                MemberFailure(id="user1", error="not found"),
                MemberFailure(id="user2", error="already member"),
            ],
        )
        assert len(r.failures) == 2
        assert r.failures[0].id == "user1"
        assert r.failures[1].error == "already member"


class TestMembersResponse:
    def test_with_roles(self):
        data = {
            "members": [
                {"userId": "u1", "creator": True},
                {"userId": "u2", "admin": True},
                {"userId": "u3"},
            ]
        }
        r = MembersResponse(**data)
        assert len(r.members) == 3
        assert r.members[0].creator is True
        assert r.members[1].admin is True
        assert r.members[2].creator is None

    def test_with_cursor(self):
        r = MembersResponse(
            members=[{"userId": "u1"}],
            cursor="abc123",
        )
        assert r.cursor == "abc123"

    def test_without_cursor(self):
        r = MembersResponse(members=[{"userId": "u1"}])
        assert r.cursor is None


class TestAdminsResponse:
    def test_with_creator(self):
        data = {
            "admins": [
                {"userId": "u1", "creator": True},
                {"userId": "u2"},
            ]
        }
        r = AdminsResponse(**data)
        assert r.admins[0].creator is True
        assert r.admins[1].creator is None


class TestUsersResponse:
    def test_from_dict(self):
        data = {"users": [{"userId": "u1"}, {"userId": "u2"}]}
        r = UsersResponse(**data)
        assert len(r.users) == 2
        assert r.users[0].user_id == "u1"


class TestErrorResponse:
    def test_from_dict(self):
        r = ErrorResponse(ok=False, description="Bad request")
        assert r.ok is False
        assert r.description == "Bad request"
