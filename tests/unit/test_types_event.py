"""Tests for vk_teams_async_bot.types.event models."""

from __future__ import annotations

import pytest

from vk_teams_async_bot.errors import EventParsingError
from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    EditedMessageEvent,
    LeftChatMembersEvent,
    NewChatMembersEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    RawUnknownEvent,
    UnpinnedMessageEvent,
    parse_event,
)
from vk_teams_async_bot.types.message import FilePart, NestedMessage


# -- Helpers --

def _chat_raw() -> dict:
    return {"chatId": "chat-1", "type": "group", "title": "Test Chat"}


def _user_raw(user_id: str = "user1") -> dict:
    return {"userId": user_id, "firstName": "Alice"}


def _wrap_event(event_type: str, payload: dict, event_id: int = 1) -> dict:
    """Wrap payload in the standard raw API structure."""
    return {"eventId": event_id, "type": event_type, "payload": payload}


# -- parse_event flattening --

class TestParseEventFlattening:
    def test_flattens_eventid_type_payload(self) -> None:
        raw = _wrap_event("newMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m1",
            "text": "hi",
            "timestamp": 1700000000,
        })
        event = parse_event(raw)
        assert isinstance(event, NewMessageEvent)
        assert event.event_id == 1
        assert event.msg_id == "m1"
        assert event.text == "hi"


# -- All 8 event types --

class TestNewMessageEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("newMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m1",
            "text": "hello",
            "timestamp": 1700000000,
        })
        event = parse_event(raw)
        assert isinstance(event, NewMessageEvent)
        assert event.chat.chat_id == "chat-1"
        assert event.from_.user_id == "user1"
        assert event.timestamp == 1700000000

    def test_with_parts(self) -> None:
        raw = _wrap_event("newMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m2",
            "text": "",
            "parts": [
                {"type": "file", "payload": {"fileId": "f1"}},
            ],
        })
        event = parse_event(raw)
        assert isinstance(event, NewMessageEvent)
        assert event.parts is not None
        assert len(event.parts) == 1
        assert isinstance(event.parts[0], FilePart)

    def test_unknown_part_skipped(self) -> None:
        raw = _wrap_event("newMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m3",
            "parts": [
                {"type": "file", "payload": {"fileId": "f1"}},
                {"type": "futureWidget", "payload": {"x": 1}},
            ],
        })
        event = parse_event(raw)
        assert isinstance(event, NewMessageEvent)
        assert event.parts is not None
        assert len(event.parts) == 1
        assert isinstance(event.parts[0], FilePart)


class TestEditedMessageEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("editedMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m1",
            "text": "edited text",
            "editedTimestamp": 1700001000,
        })
        event = parse_event(raw)
        assert isinstance(event, EditedMessageEvent)
        assert event.edited_timestamp == 1700001000
        assert event.text == "edited text"


class TestDeletedMessageEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("deletedMessage", {
            "chat": _chat_raw(),
            "msgId": "m1",
            "timestamp": 1700000000,
        })
        event = parse_event(raw)
        assert isinstance(event, DeletedMessageEvent)
        assert event.msg_id == "m1"


class TestPinnedMessageEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("pinnedMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "msgId": "m1",
            "text": "pinned text",
            "timestamp": 1700000000,
        })
        event = parse_event(raw)
        assert isinstance(event, PinnedMessageEvent)
        assert event.text == "pinned text"


class TestUnpinnedMessageEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("unpinnedMessage", {
            "chat": _chat_raw(),
            "msgId": "m1",
            "timestamp": 1700000000,
        })
        event = parse_event(raw)
        assert isinstance(event, UnpinnedMessageEvent)
        assert event.msg_id == "m1"


class TestNewChatMembersEvent:
    def test_added_by_preserved(self) -> None:
        raw = _wrap_event("newChatMembers", {
            "chat": _chat_raw(),
            "newMembers": [_user_raw("new1"), _user_raw("new2")],
            "addedBy": _user_raw("admin1"),
        })
        event = parse_event(raw)
        assert isinstance(event, NewChatMembersEvent)
        assert len(event.new_members) == 2
        assert event.new_members[0].user_id == "new1"
        assert event.added_by.user_id == "admin1"


class TestLeftChatMembersEvent:
    def test_removed_by_preserved(self) -> None:
        raw = _wrap_event("leftChatMembers", {
            "chat": _chat_raw(),
            "leftMembers": [_user_raw("gone1")],
            "removedBy": _user_raw("admin1"),
        })
        event = parse_event(raw)
        assert isinstance(event, LeftChatMembersEvent)
        assert len(event.left_members) == 1
        assert event.left_members[0].user_id == "gone1"
        assert event.removed_by.user_id == "admin1"


class TestCallbackQueryEvent:
    def test_basic(self) -> None:
        raw = _wrap_event("callbackQuery", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "queryId": "q1",
            "callbackData": "btn_ok",
        })
        event = parse_event(raw)
        assert isinstance(event, CallbackQueryEvent)
        assert event.query_id == "q1"
        assert event.callback_data == "btn_ok"
        assert event.message is None

    def test_with_message(self) -> None:
        raw = _wrap_event("callbackQuery", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "queryId": "q2",
            "callbackData": "btn_cancel",
            "message": {
                "from": _user_raw("bot1"),
                "msgId": "m-orig",
                "text": "Choose an option",
                "timestamp": 1700000000,
            },
        })
        event = parse_event(raw)
        assert isinstance(event, CallbackQueryEvent)
        assert event.message is not None
        assert isinstance(event.message, NestedMessage)
        assert event.message.msg_id == "m-orig"
        assert event.message.from_.user_id == "bot1"


# -- Unknown and error cases --

class TestUnknownEvent:
    def test_unknown_type_returns_raw(self) -> None:
        raw = _wrap_event("superNewEvent", {"data": 42}, event_id=99)
        event = parse_event(raw)
        assert isinstance(event, RawUnknownEvent)
        assert event.event_id == 99
        assert event.type == "superNewEvent"
        assert event.payload == {"data": 42}


class TestMalformedEvent:
    def test_missing_required_field_raises(self) -> None:
        # newMessage requires msgId
        raw = _wrap_event("newMessage", {
            "chat": _chat_raw(),
            "from": _user_raw(),
            "text": "no msgId here",
        })
        with pytest.raises(EventParsingError) as exc_info:
            parse_event(raw)
        assert exc_info.value.raw_data == raw

    def test_error_contains_raw_data(self) -> None:
        raw = _wrap_event("editedMessage", {
            "chat": _chat_raw(),
            # missing from and msgId
        })
        with pytest.raises(EventParsingError) as exc_info:
            parse_event(raw)
        assert exc_info.value.raw_data is not None
        assert exc_info.value.raw_data["type"] == "editedMessage"
