"""Comprehensive tests for the methods/ package.

Tests mock at the session level (session.get / session.post) and verify
that each method:
  - calls the correct endpoint with the right parameters
  - returns the correct Pydantic model type
  - enforces validation rules (mutual exclusions, etc.)
"""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vk_teams_async_bot.methods._helpers import bool_str
from vk_teams_async_bot.methods.chats import ChatMethods
from vk_teams_async_bot.methods.events import EventMethods
from vk_teams_async_bot.methods.files import FileMethods
from vk_teams_async_bot.methods.messages import MessageMethods
from vk_teams_async_bot.methods.self_ import SelfMethods
from vk_teams_async_bot.types.chat import (
    ChatInfoChannel,
    ChatInfoGroup,
    ChatInfoPrivate,
)
from vk_teams_async_bot.types.enums import ChatAction, ParseMode
from vk_teams_async_bot.types.event import (
    BaseEvent,
    CallbackQueryEvent,
    NewMessageEvent,
    RawUnknownEvent,
)
from vk_teams_async_bot.types.file import FileInfo
from vk_teams_async_bot.types.response import (
    AdminsResponse,
    ChatCreateResponse,
    FileUploadResponse,
    MembersResponse,
    MessageResponse,
    OkResponse,
    OkWithDescriptionResponse,
    PartialSuccessResponse,
    UsersResponse,
)
from vk_teams_async_bot.types.user import BotInfo

# ===================================================================
# bool_str helper
# ===================================================================


class TestBoolStr:
    def test_true(self):
        assert bool_str(True) == "true"

    def test_false(self):
        assert bool_str(False) == "false"

    def test_none(self):
        assert bool_str(None) is None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mixin(cls):
    """Create a mixin instance with a mocked session."""
    obj = cls.__new__(cls)
    session = MagicMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    session._ensure_session = AsyncMock()
    obj._session = session
    return obj


@pytest.fixture
def self_mixin():
    return _make_mixin(SelfMethods)


@pytest.fixture
def msg_mixin():
    return _make_mixin(MessageMethods)


@pytest.fixture
def chat_mixin():
    return _make_mixin(ChatMethods)


@pytest.fixture
def file_mixin():
    return _make_mixin(FileMethods)


@pytest.fixture
def event_mixin():
    return _make_mixin(EventMethods)


# ===================================================================
# SelfMethods
# ===================================================================


class TestGetSelf:
    @pytest.mark.asyncio
    async def test_happy_path(self, self_mixin):
        self_mixin._session.get.return_value = {
            "userId": "bot123",
            "nick": "testbot",
            "firstName": "Test",
            "about": "A test bot",
            "photo": [{"url": "https://example.com/photo.png"}],
            "ok": True,
        }

        result = await self_mixin.get_self()

        self_mixin._session.get.assert_awaited_once_with("/self/get")
        assert isinstance(result, BotInfo)
        assert result.user_id == "bot123"
        assert result.nick == "testbot"
        assert result.first_name == "Test"
        assert result.about == "A test bot"
        assert len(result.photo) == 1


# ===================================================================
# MessageMethods
# ===================================================================


class TestSendText:
    @pytest.mark.asyncio
    async def test_happy_path(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "100"}

        result = await msg_mixin.send_text("chat1", "Hello!")

        msg_mixin._session.get.assert_awaited_once()
        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/sendText"
        assert call_kwargs[1]["chatId"] == "chat1"
        assert call_kwargs[1]["text"] == "Hello!"
        assert isinstance(result, MessageResponse)
        assert result.msg_id == "100"

    @pytest.mark.asyncio
    async def test_with_all_params(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "101"}

        result = await msg_mixin.send_text(
            "chat1",
            "Hello!",
            reply_msg_id=[1, 2],
            inline_keyboard_markup="[[]]",
            parse_mode=ParseMode.HTML,
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["replyMsgId"] == [1, 2]
        assert call_kwargs["inlineKeyboardMarkup"] == "[[]]"
        assert call_kwargs["parseMode"] == "HTML"
        assert isinstance(result, MessageResponse)

    @pytest.mark.asyncio
    async def test_with_reply(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "102"}

        result = await msg_mixin.send_text("chat1", "reply test", reply_msg_id=[5])

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["replyMsgId"] == [5]
        assert isinstance(result, MessageResponse)

    @pytest.mark.asyncio
    async def test_with_forward(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "103"}

        result = await msg_mixin.send_text(
            "chat1",
            "forward test",
            forward_chat_id="other_chat",
            forward_msg_id=[10],
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["forwardChatId"] == "other_chat"
        assert call_kwargs["forwardMsgId"] == [10]
        assert isinstance(result, MessageResponse)

    @pytest.mark.asyncio
    async def test_reply_and_forward_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_text(
                "chat1",
                "bad",
                reply_msg_id=[1],
                forward_chat_id="other",
                forward_msg_id=[2],
            )

    @pytest.mark.asyncio
    async def test_forward_chat_without_msg_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="together"):
            await msg_mixin.send_text("chat1", "bad", forward_chat_id="other")

    @pytest.mark.asyncio
    async def test_forward_msg_without_chat_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="together"):
            await msg_mixin.send_text("chat1", "bad", forward_msg_id=[1])

    @pytest.mark.asyncio
    async def test_parse_mode_and_format_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_text(
                "chat1",
                "bad",
                parse_mode=ParseMode.HTML,
                format_={"bold": []},
            )

    @pytest.mark.asyncio
    async def test_with_format_dict(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "104"}

        await msg_mixin.send_text(
            "chat1", "formatted", format_={"bold": [{"offset": 0, "length": 4}]}
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["format"] == json.dumps(
            {"bold": [{"offset": 0, "length": 4}]}
        )

    @pytest.mark.asyncio
    async def test_with_format_object(self, msg_mixin):
        """Test with an object that has a .to_json() method."""
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "105"}

        mock_format = MagicMock()
        mock_format.to_json.return_value = '{"bold":[]}'

        await msg_mixin.send_text("chat1", "fmt", format_=mock_format)

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["format"] == '{"bold":[]}'

    @pytest.mark.asyncio
    async def test_with_keyboard_object(self, msg_mixin):
        """Test with a keyboard object that has .to_json()."""
        msg_mixin._session.get.return_value = {"ok": True, "msgId": "106"}

        mock_kb = MagicMock()
        mock_kb.to_json.return_value = '[[{"text":"OK"}]]'

        await msg_mixin.send_text("chat1", "kb", inline_keyboard_markup=mock_kb)

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["inlineKeyboardMarkup"] == '[[{"text":"OK"}]]'


class TestSendFile:
    @pytest.mark.asyncio
    async def test_with_file_id(self, msg_mixin):
        msg_mixin._session.get.return_value = {
            "ok": True,
            "msgId": "200",
            "fileId": "abc123",
        }

        result = await msg_mixin.send_file("chat1", file_id="abc123", caption="My file")

        msg_mixin._session.get.assert_awaited_once()
        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/sendFile"
        assert call_kwargs[1]["fileId"] == "abc123"
        assert call_kwargs[1]["caption"] == "My file"
        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_with_file_upload(self, msg_mixin, tmp_path):
        msg_mixin._session.post.return_value = {
            "ok": True,
            "fileId": "new_file_id",
            "msgId": "201",
        }

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        result = await msg_mixin.send_file(
            "chat1", file=str(test_file), caption="Uploaded"
        )

        msg_mixin._session.post.assert_awaited_once()
        call_args = msg_mixin._session.post.call_args
        assert call_args[0][0] == "/messages/sendFile"
        assert call_args[1]["chatId"] == "chat1"
        assert call_args[1]["caption"] == "Uploaded"
        assert isinstance(result, FileUploadResponse)
        assert result.file_id == "new_file_id"

    @pytest.mark.asyncio
    async def test_with_file_tuple(self, msg_mixin):
        msg_mixin._session.post.return_value = {
            "ok": True,
            "fileId": "tuple_file",
            "msgId": "202",
        }

        file_obj = BytesIO(b"content")
        result = await msg_mixin.send_file(
            "chat1",
            file=("test.txt", file_obj, "text/plain"),
        )

        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_both_file_id_and_file_raises(self, msg_mixin, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")

        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_file("chat1", file_id="abc", file=str(test_file))

    @pytest.mark.asyncio
    async def test_neither_file_id_nor_file_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="must be provided"):
            await msg_mixin.send_file("chat1")

    @pytest.mark.asyncio
    async def test_with_all_get_params(self, msg_mixin):
        msg_mixin._session.get.return_value = {
            "ok": True,
            "msgId": "203",
            "fileId": "fid",
        }

        result = await msg_mixin.send_file(
            "chat1",
            file_id="fid",
            caption="cap",
            reply_msg_id=[1],
            inline_keyboard_markup="[[]]",
            parse_mode=ParseMode.MARKDOWNV2,
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["fileId"] == "fid"
        assert call_kwargs["caption"] == "cap"
        assert call_kwargs["replyMsgId"] == [1]
        assert call_kwargs["parseMode"] == "MarkdownV2"
        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_send_file_reply_and_forward_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_file(
                "chat1",
                file_id="fid",
                reply_msg_id=[1],
                forward_chat_id="c",
                forward_msg_id=[2],
            )

    @pytest.mark.asyncio
    async def test_send_file_parse_and_format_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_file(
                "chat1",
                file_id="fid",
                parse_mode=ParseMode.HTML,
                format_={"bold": []},
            )


class TestSendVoice:
    @pytest.mark.asyncio
    async def test_with_file_id(self, msg_mixin):
        msg_mixin._session.get.return_value = {
            "ok": True,
            "msgId": "300",
            "fileId": "voice123",
        }

        result = await msg_mixin.send_voice("chat1", file_id="voice123")

        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/sendVoice"
        assert call_kwargs[1]["fileId"] == "voice123"
        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_with_file_upload(self, msg_mixin, tmp_path):
        msg_mixin._session.post.return_value = {
            "ok": True,
            "fileId": "voice_new",
            "msgId": "301",
        }

        voice = tmp_path / "voice.ogg"
        voice.write_bytes(b"\x00" * 100)

        result = await msg_mixin.send_voice("chat1", file=str(voice))

        msg_mixin._session.post.assert_awaited_once()
        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_both_raises(self, msg_mixin, tmp_path):
        voice = tmp_path / "v.ogg"
        voice.write_bytes(b"\x00")

        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_voice("chat1", file_id="abc", file=str(voice))

    @pytest.mark.asyncio
    async def test_neither_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="must be provided"):
            await msg_mixin.send_voice("chat1")

    @pytest.mark.asyncio
    async def test_with_forward(self, msg_mixin):
        msg_mixin._session.get.return_value = {
            "ok": True,
            "msgId": "302",
            "fileId": "v1",
        }

        result = await msg_mixin.send_voice(
            "chat1",
            file_id="v1",
            forward_chat_id="other",
            forward_msg_id=[5],
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["forwardChatId"] == "other"
        assert isinstance(result, FileUploadResponse)

    @pytest.mark.asyncio
    async def test_reply_and_forward_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.send_voice(
                "chat1",
                file_id="v1",
                reply_msg_id=[1],
                forward_chat_id="c",
                forward_msg_id=[2],
            )


class TestEditText:
    @pytest.mark.asyncio
    async def test_happy_path(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        result = await msg_mixin.edit_text("chat1", 42, "Updated text")

        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/editText"
        assert call_kwargs[1]["chatId"] == "chat1"
        assert call_kwargs[1]["msgId"] == 42
        assert call_kwargs[1]["text"] == "Updated text"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_with_all_params(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        mock_kb = MagicMock()
        mock_kb.to_json.return_value = "[]"

        result = await msg_mixin.edit_text(
            "chat1",
            42,
            "Edited",
            inline_keyboard_markup=mock_kb,
            parse_mode=ParseMode.HTML,
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["parseMode"] == "HTML"
        assert call_kwargs["inlineKeyboardMarkup"] == "[]"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_parse_mode_and_format_raises(self, msg_mixin):
        with pytest.raises(ValueError, match="mutually exclusive"):
            await msg_mixin.edit_text(
                "chat1",
                42,
                "bad",
                parse_mode=ParseMode.HTML,
                format_={"bold": []},
            )


class TestDeleteMessages:
    @pytest.mark.asyncio
    async def test_happy_path(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        result = await msg_mixin.delete_messages("chat1", 42)

        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/deleteMessages"
        assert call_kwargs[1]["msgId"] == 42
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_with_list(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        result = await msg_mixin.delete_messages("chat1", [1, 2, 3])

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["msgId"] == [1, 2, 3]
        assert isinstance(result, OkResponse)


class TestAnswerCallbackQuery:
    @pytest.mark.asyncio
    async def test_happy_path(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        result = await msg_mixin.answer_callback_query("qid_123")

        call_kwargs = msg_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/messages/answerCallbackQuery"
        assert call_kwargs[1]["queryId"] == "qid_123"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_with_all_params(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        result = await msg_mixin.answer_callback_query(
            "qid_456",
            text="Done!",
            show_alert=True,
            url="https://example.com",
        )

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["text"] == "Done!"
        assert call_kwargs["showAlert"] == "true"
        assert call_kwargs["url"] == "https://example.com"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_show_alert_false(self, msg_mixin):
        msg_mixin._session.get.return_value = {"ok": True}

        await msg_mixin.answer_callback_query("qid", show_alert=False)

        call_kwargs = msg_mixin._session.get.call_args[1]
        assert call_kwargs["showAlert"] == "false"


class TestDownloadFile:
    @pytest.mark.asyncio
    async def test_returns_bytes(self, msg_mixin):
        msg_mixin._session.download = AsyncMock(return_value=b"file content bytes")

        result = await msg_mixin.download_file("https://files.example.com/f1")

        assert result == b"file content bytes"
        msg_mixin._session.download.assert_awaited_once_with(
            "https://files.example.com/f1"
        )

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, msg_mixin):
        from vk_teams_async_bot.errors import APIError

        msg_mixin._session.download = AsyncMock(
            side_effect=APIError(
                404, "HTTP 404 downloading https://files.example.com/f1"
            )
        )
        with pytest.raises(APIError):
            await msg_mixin.download_file("https://files.example.com/f1")


# ===================================================================
# ChatMethods
# ===================================================================


class TestCreateChat:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"sn": "new_chat_id"}

        result = await chat_mixin.create_chat("My Chat")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/createChat"
        assert call_kwargs[1]["name"] == "My Chat"
        assert isinstance(result, ChatCreateResponse)
        assert result.sn == "new_chat_id"

    @pytest.mark.asyncio
    async def test_with_all_params(self, chat_mixin):
        chat_mixin._session.get.return_value = {"sn": "chat_full"}

        result = await chat_mixin.create_chat(
            "Full Chat",
            about="Description",
            rules="Be nice",
            members=["user1", "user2"],
            public=True,
            default_role="member",
            join_moderation=False,
        )

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["name"] == "Full Chat"
        assert call_kwargs["about"] == "Description"
        assert call_kwargs["rules"] == "Be nice"
        assert call_kwargs["members"] == json.dumps([{"sn": "user1"}, {"sn": "user2"}])
        assert call_kwargs["public"] == "true"
        assert call_kwargs["defaultRole"] == "member"
        assert call_kwargs["joinModeration"] == "false"
        assert isinstance(result, ChatCreateResponse)


class TestSetChatAvatar:
    @pytest.mark.asyncio
    async def test_with_tuple(self, chat_mixin):
        chat_mixin._session.post.return_value = {
            "ok": True,
            "description": "Avatar set",
        }

        file_obj = BytesIO(b"\x89PNG")
        result = await chat_mixin.set_chat_avatar(
            "chat1", ("avatar.png", file_obj, "image/png")
        )

        chat_mixin._session.post.assert_awaited_once()
        call_args = chat_mixin._session.post.call_args
        assert call_args[0][0] == "/chats/avatar/set"
        assert call_args[1]["chatId"] == "chat1"
        assert isinstance(result, OkWithDescriptionResponse)
        assert result.description == "Avatar set"


class TestAddChatMembers:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.add_chat_members("chat1", ["user1", "user2"])

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["members"] == json.dumps([{"sn": "user1"}, {"sn": "user2"}])
        assert isinstance(result, PartialSuccessResponse)

    @pytest.mark.asyncio
    async def test_with_failures(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "ok": True,
            "failures": [{"id": "user2", "error": "User not found"}],
        }

        result = await chat_mixin.add_chat_members("chat1", ["user1", "user2"])

        assert isinstance(result, PartialSuccessResponse)
        assert len(result.failures) == 1
        assert result.failures[0].id == "user2"


class TestDeleteChatMembers:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.delete_chat_members("chat1", ["user1"])

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/members/delete"
        assert isinstance(result, OkResponse)


class TestSendChatActions:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.send_chat_actions("chat1", [ChatAction.TYPING])

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/sendActions"
        assert call_kwargs[1]["actions"] == "typing"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_multiple_actions(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        await chat_mixin.send_chat_actions(
            "chat1", [ChatAction.TYPING, ChatAction.LOOKING]
        )

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["actions"] == "typing,looking"


class TestGetChatInfo:
    @pytest.mark.asyncio
    async def test_private_chat(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "type": "private",
            "firstName": "Alice",
            "lastName": "Smith",
            "nick": "alice",
            "about": "Hi",
            "isBot": False,
        }

        result = await chat_mixin.get_chat_info("alice@example.com")

        assert isinstance(result, ChatInfoPrivate)
        assert result.first_name == "Alice"
        assert result.is_bot is False

    @pytest.mark.asyncio
    async def test_group_chat(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "type": "group",
            "title": "Dev Team",
            "about": "Development",
            "rules": "Be kind",
            "public": True,
        }

        result = await chat_mixin.get_chat_info("chat_group_id")

        assert isinstance(result, ChatInfoGroup)
        assert result.title == "Dev Team"

    @pytest.mark.asyncio
    async def test_channel(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "type": "channel",
            "title": "Announcements",
            "about": "News",
            "public": False,
        }

        result = await chat_mixin.get_chat_info("channel_id")

        assert isinstance(result, ChatInfoChannel)
        assert result.title == "Announcements"


class TestGetChatAdmins:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "admins": [
                {"userId": "admin1", "creator": True},
                {"userId": "admin2"},
            ]
        }

        result = await chat_mixin.get_chat_admins("chat1")

        assert isinstance(result, AdminsResponse)
        assert len(result.admins) == 2
        assert result.admins[0].user_id == "admin1"
        assert result.admins[0].creator is True


class TestGetChatMembers:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "members": [
                {"userId": "m1"},
                {"userId": "m2", "admin": True},
            ],
            "cursor": "next_page",
        }

        result = await chat_mixin.get_chat_members("chat1")

        assert isinstance(result, MembersResponse)
        assert len(result.members) == 2
        assert result.cursor == "next_page"

    @pytest.mark.asyncio
    async def test_with_cursor(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "members": [{"userId": "m3"}],
        }

        result = await chat_mixin.get_chat_members("chat1", cursor="page2")

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["cursor"] == "page2"
        assert isinstance(result, MembersResponse)


class TestGetBlockedUsers:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"users": [{"userId": "blocked1"}]}

        result = await chat_mixin.get_blocked_users("chat1")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/getBlockedUsers"
        assert isinstance(result, UsersResponse)
        assert len(result.users) == 1


class TestGetPendingUsers:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {
            "users": [{"userId": "pending1"}, {"userId": "pending2"}]
        }

        result = await chat_mixin.get_pending_users("chat1")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/getPendingUsers"
        assert isinstance(result, UsersResponse)
        assert len(result.users) == 2


class TestBlockUser:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.block_user("chat1", "baduser")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/blockUser"
        assert call_kwargs[1]["userId"] == "baduser"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_with_del_messages(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        await chat_mixin.block_user("chat1", "baduser", del_last_messages=True)

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["delLastMessages"] == "true"


class TestUnblockUser:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.unblock_user("chat1", "user1")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/unblockUser"
        assert call_kwargs[1]["userId"] == "user1"
        assert isinstance(result, OkResponse)


class TestResolvePending:
    @pytest.mark.asyncio
    async def test_with_user_id(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.resolve_pending("chat1", True, user_id="user1")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/resolvePending"
        assert call_kwargs[1]["approve"] == "true"
        assert call_kwargs[1]["userId"] == "user1"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_with_everyone(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.resolve_pending("chat1", False, everyone=True)

        call_kwargs = chat_mixin._session.get.call_args[1]
        assert call_kwargs["approve"] == "false"
        assert call_kwargs["everyone"] == "true"
        assert isinstance(result, OkResponse)

    @pytest.mark.asyncio
    async def test_both_raises(self, chat_mixin):
        with pytest.raises(ValueError, match="Exactly one"):
            await chat_mixin.resolve_pending("chat1", True, user_id="u1", everyone=True)

    @pytest.mark.asyncio
    async def test_neither_raises(self, chat_mixin):
        with pytest.raises(ValueError, match="Exactly one"):
            await chat_mixin.resolve_pending("chat1", True)


class TestSetChatTitle:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.set_chat_title("chat1", "New Title")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/setTitle"
        assert call_kwargs[1]["title"] == "New Title"
        assert isinstance(result, OkResponse)


class TestSetChatAbout:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.set_chat_about("chat1", "New Description")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/setAbout"
        assert call_kwargs[1]["about"] == "New Description"
        assert isinstance(result, OkResponse)


class TestSetChatRules:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.set_chat_rules("chat1", "New Rules")

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/setRules"
        assert call_kwargs[1]["rules"] == "New Rules"
        assert isinstance(result, OkResponse)


class TestPinMessage:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.pin_message("chat1", 99)

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/pinMessage"
        assert call_kwargs[1]["msgId"] == 99
        assert isinstance(result, OkResponse)


class TestUnpinMessage:
    @pytest.mark.asyncio
    async def test_happy_path(self, chat_mixin):
        chat_mixin._session.get.return_value = {"ok": True}

        result = await chat_mixin.unpin_message("chat1", 99)

        call_kwargs = chat_mixin._session.get.call_args
        assert call_kwargs[0][0] == "/chats/unpinMessage"
        assert call_kwargs[1]["msgId"] == 99
        assert isinstance(result, OkResponse)


# ===================================================================
# FileMethods
# ===================================================================


class TestGetFileInfo:
    @pytest.mark.asyncio
    async def test_happy_path(self, file_mixin):
        file_mixin._session.get.return_value = {
            "type": "video",
            "size": 20971520,
            "filename": "VIDEO.mkv",
            "url": "https://example.com/get/file123",
        }

        result = await file_mixin.get_file_info("file_abc")

        file_mixin._session.get.assert_awaited_once_with(
            "/files/getInfo", fileId="file_abc"
        )
        assert isinstance(result, FileInfo)
        assert result.type == "video"
        assert result.size == 20971520
        assert result.filename == "VIDEO.mkv"
        assert result.url == "https://example.com/get/file123"


# ===================================================================
# EventMethods
# ===================================================================


class TestGetEvents:
    @pytest.mark.asyncio
    async def test_happy_path_with_multiple_types(self, event_mixin):
        event_mixin._session.get.return_value = {
            "ok": True,
            "events": [
                {
                    "eventId": 1,
                    "type": "newMessage",
                    "payload": {
                        "msgId": "m1",
                        "chat": {
                            "chatId": "chat1",
                            "type": "private",
                        },
                        "from": {
                            "userId": "user1",
                            "firstName": "Alice",
                        },
                        "text": "Hello",
                        "timestamp": 1234567890,
                    },
                },
                {
                    "eventId": 2,
                    "type": "callbackQuery",
                    "payload": {
                        "queryId": "q1",
                        "chat": {
                            "chatId": "chat2",
                            "type": "group",
                        },
                        "from": {
                            "userId": "user2",
                        },
                        "callbackData": "btn_click",
                    },
                },
                {
                    "eventId": 3,
                    "type": "unknownFutureType",
                    "payload": {"data": "something"},
                },
            ],
        }

        result = await event_mixin.get_events(0, 15)

        event_mixin._session.get.assert_awaited_once_with(
            "/events/get", lastEventId=0, pollTime=15
        )
        assert len(result) == 3
        assert isinstance(result[0], NewMessageEvent)
        assert result[0].text == "Hello"
        assert isinstance(result[1], CallbackQueryEvent)
        assert result[1].callback_data == "btn_click"
        assert isinstance(result[2], RawUnknownEvent)
        assert result[2].type == "unknownFutureType"

    @pytest.mark.asyncio
    async def test_empty_events(self, event_mixin):
        event_mixin._session.get.return_value = {
            "ok": True,
            "events": [],
        }

        result = await event_mixin.get_events(5, 10)

        assert result == []

    @pytest.mark.asyncio
    async def test_missing_events_key(self, event_mixin):
        event_mixin._session.get.return_value = {"ok": True}

        result = await event_mixin.get_events(0, 10)

        assert result == []
