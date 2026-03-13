import pytest
from pydantic import TypeAdapter, ValidationError

from vk_teams_async_bot.types.chat import (
    ChatInfoChannel,
    ChatInfoGroup,
    ChatInfoPrivate,
    ChatInfoResponse,
)
from vk_teams_async_bot.types.event_chat import EventChatRef


class TestChatInfoPrivate:
    def test_from_dict(self):
        data = {
            "type": "private",
            "firstName": "John",
            "lastName": "Doe",
            "nick": "jdoe",
            "about": "Hello",
            "isBot": False,
            "language": "en",
        }
        chat = ChatInfoPrivate(**data)
        assert chat.type == "private"
        assert chat.first_name == "John"
        assert chat.is_bot is False
        assert chat.language == "en"

    def test_minimal(self):
        chat = ChatInfoPrivate(type="private")
        assert chat.first_name is None


class TestChatInfoGroup:
    def test_from_dict(self):
        data = {
            "type": "group",
            "title": "My Group",
            "about": "A group",
            "rules": "Be nice",
            "inviteLink": "https://example.com/join",
            "public": True,
            "joinModeration": False,
        }
        chat = ChatInfoGroup(**data)
        assert chat.type == "group"
        assert chat.title == "My Group"
        assert chat.invite_link == "https://example.com/join"
        assert chat.public is True


class TestChatInfoChannel:
    def test_from_dict(self):
        data = {
            "type": "channel",
            "title": "My Channel",
        }
        chat = ChatInfoChannel(**data)
        assert chat.type == "channel"
        assert chat.title == "My Channel"


class TestChatInfoResponseDiscriminator:
    def test_private(self):
        adapter = TypeAdapter(ChatInfoResponse)
        result = adapter.validate_python({"type": "private", "firstName": "John"})
        assert isinstance(result, ChatInfoPrivate)

    def test_group(self):
        adapter = TypeAdapter(ChatInfoResponse)
        result = adapter.validate_python({"type": "group", "title": "Grp"})
        assert isinstance(result, ChatInfoGroup)

    def test_channel(self):
        adapter = TypeAdapter(ChatInfoResponse)
        result = adapter.validate_python({"type": "channel", "title": "Ch"})
        assert isinstance(result, ChatInfoChannel)

    def test_invalid_type(self):
        adapter = TypeAdapter(ChatInfoResponse)
        with pytest.raises(ValidationError):
            adapter.validate_python({"type": "unknown"})


class TestEventChatRefDistinctFromChatInfo:
    def test_event_chat_ref_has_chat_id(self):
        ref = EventChatRef(chatId="123@chat.agent", type="group", title="Grp")
        assert ref.chat_id == "123@chat.agent"
        assert ref.type == "group"

    def test_types_are_distinct(self):
        assert EventChatRef is not ChatInfoPrivate
        assert EventChatRef is not ChatInfoGroup
        assert EventChatRef is not ChatInfoChannel

    def test_event_chat_ref_extra_allowed(self):
        ref = EventChatRef(chatId="123", type="private", unknown="ok")
        assert ref.chat_id == "123"

    def test_chat_info_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ChatInfoPrivate(type="private", unknown="nope")
