"""Tests for vk_teams_async_bot.utils — extract_chat_user."""

from __future__ import annotations

from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    EditedMessageEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    RawUnknownEvent,
    UnpinnedMessageEvent,
    parse_event,
)
from vk_teams_async_bot.utils import extract_chat_user


# -- Helpers --


def _chat_raw() -> dict:
    return {"chatId": "chat-1", "type": "group", "title": "Test Chat"}


def _user_raw(user_id: str = "user1") -> dict:
    return {"userId": user_id, "firstName": "Alice"}


def _wrap_event(event_type: str, payload: dict, event_id: int = 1) -> dict:
    return {"eventId": event_id, "type": event_type, "payload": payload}


# -- Tests --


class TestExtractChatUser:
    def test_new_message_returns_tuple(self) -> None:
        raw = _wrap_event(
            "newMessage",
            {
                "chat": _chat_raw(),
                "from": _user_raw("sender1"),
                "msgId": "m1",
                "text": "hello",
            },
        )
        event = parse_event(raw)
        assert isinstance(event, NewMessageEvent)

        result = extract_chat_user(event)
        assert result == ("chat-1", "sender1")

    def test_edited_message_returns_tuple(self) -> None:
        raw = _wrap_event(
            "editedMessage",
            {
                "chat": _chat_raw(),
                "from": _user_raw("editor1"),
                "msgId": "m2",
                "text": "edited",
                "editedTimestamp": 1700001000,
            },
        )
        event = parse_event(raw)
        assert isinstance(event, EditedMessageEvent)

        result = extract_chat_user(event)
        assert result == ("chat-1", "editor1")

    def test_pinned_message_returns_tuple(self) -> None:
        raw = _wrap_event(
            "pinnedMessage",
            {
                "chat": _chat_raw(),
                "from": _user_raw("pinner1"),
                "msgId": "m3",
                "text": "pinned",
            },
        )
        event = parse_event(raw)
        assert isinstance(event, PinnedMessageEvent)

        result = extract_chat_user(event)
        assert result == ("chat-1", "pinner1")

    def test_callback_query_with_chat_returns_tuple(self) -> None:
        raw = _wrap_event(
            "callbackQuery",
            {
                "chat": _chat_raw(),
                "from": _user_raw("clicker1"),
                "queryId": "q1",
                "callbackData": "btn_ok",
            },
        )
        event = parse_event(raw)
        assert isinstance(event, CallbackQueryEvent)
        assert event.chat is not None

        result = extract_chat_user(event)
        assert result == ("chat-1", "clicker1")

    def test_callback_query_without_chat_returns_none(self) -> None:
        """CallbackQuery with no chat and no message -> chat stays None."""
        event = CallbackQueryEvent(
            eventId=10,
            type="callbackQuery",
            **{"from": _user_raw("clicker2")},
            queryId="q2",
            callbackData="btn_cancel",
            chat=None,
            message=None,
        )
        assert event.chat is None

        result = extract_chat_user(event)
        assert result is None

    def test_deleted_message_returns_none(self) -> None:
        raw = _wrap_event(
            "deletedMessage",
            {
                "chat": _chat_raw(),
                "msgId": "m4",
                "timestamp": 1700000000,
            },
        )
        event = parse_event(raw)
        assert isinstance(event, DeletedMessageEvent)

        result = extract_chat_user(event)
        assert result is None

    def test_unpinned_message_returns_none(self) -> None:
        raw = _wrap_event(
            "unpinnedMessage",
            {
                "chat": _chat_raw(),
                "msgId": "m5",
                "timestamp": 1700000000,
            },
        )
        event = parse_event(raw)
        assert isinstance(event, UnpinnedMessageEvent)

        result = extract_chat_user(event)
        assert result is None

    def test_raw_unknown_event_returns_none(self) -> None:
        raw = _wrap_event(
            "superNewEvent",
            {"data": 42},
            event_id=99,
        )
        event = parse_event(raw)
        assert isinstance(event, RawUnknownEvent)

        result = extract_chat_user(event)
        assert result is None
