"""Shared event construction helpers for integration and E2E tests."""

from __future__ import annotations

from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    EditedMessageEvent,
    LeftChatMembersEvent,
    NewChatMembersEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    UnpinnedMessageEvent,
    parse_event,
)


def make_new_message_event(
    text: str = "hello",
    event_id: int = 1,
    chat_id: str = "chat1",
    user_id: str = "user1",
    chat_type: str = "private",
) -> NewMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "newMessage",
        "payload": {
            "msgId": "msg1",
            "chat": {"chatId": chat_id, "type": chat_type, "title": ""},
            "from": {"userId": user_id, "firstName": "Test"},
            "text": text,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, NewMessageEvent)
    return event


def make_edited_message_event(
    text: str = "edited",
    event_id: int = 1,
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> EditedMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "editedMessage",
        "payload": {
            "msgId": "msg1",
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "from": {"userId": user_id, "firstName": "Test"},
            "text": text,
            "timestamp": 1000,
            "editedTimestamp": 1001,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, EditedMessageEvent)
    return event


def make_callback_event(
    callback_data: str = "btn1",
    event_id: int = 2,
    include_message: bool = False,
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> CallbackQueryEvent:
    raw = {
        "eventId": event_id,
        "type": "callbackQuery",
        "payload": {
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "from": {"userId": user_id, "firstName": "Test"},
            "queryId": "q1",
            "callbackData": callback_data,
        },
    }
    if include_message:
        raw["payload"]["message"] = {
            "msgId": "msg_in_cb",
            "from": {"userId": user_id, "firstName": "Test"},
            "text": "original message",
            "timestamp": 999,
        }
    event = parse_event(raw)
    assert isinstance(event, CallbackQueryEvent)
    return event


def make_deleted_event(
    event_id: int = 3,
    chat_id: str = "chat1",
    msg_id: str = "msg1",
) -> DeletedMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "deletedMessage",
        "payload": {
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "msgId": msg_id,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, DeletedMessageEvent)
    return event


def make_pinned_event(
    text: str = "pinned text",
    event_id: int = 4,
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> PinnedMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "pinnedMessage",
        "payload": {
            "msgId": "msg1",
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "from": {"userId": user_id, "firstName": "Test"},
            "text": text,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, PinnedMessageEvent)
    return event


def make_unpinned_event(
    event_id: int = 5,
    chat_id: str = "chat1",
    msg_id: str = "msg1",
) -> UnpinnedMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "unpinnedMessage",
        "payload": {
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "msgId": msg_id,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, UnpinnedMessageEvent)
    return event


def make_new_chat_members_event(
    event_id: int = 6,
    chat_id: str = "chat1",
    members: list[dict] | None = None,
    added_by: dict | None = None,
) -> NewChatMembersEvent:
    if members is None:
        members = [{"userId": "new_user1", "firstName": "New"}]
    if added_by is None:
        added_by = {"userId": "admin1", "firstName": "Admin"}
    raw = {
        "eventId": event_id,
        "type": "newChatMembers",
        "payload": {
            "chat": {"chatId": chat_id, "type": "group", "title": "Test Group"},
            "newMembers": members,
            "addedBy": added_by,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, NewChatMembersEvent)
    return event


def make_left_chat_members_event(
    event_id: int = 7,
    chat_id: str = "chat1",
    members: list[dict] | None = None,
    removed_by: dict | None = None,
) -> LeftChatMembersEvent:
    if members is None:
        members = [{"userId": "left_user1", "firstName": "Left"}]
    if removed_by is None:
        removed_by = {"userId": "admin1", "firstName": "Admin"}
    raw = {
        "eventId": event_id,
        "type": "leftChatMembers",
        "payload": {
            "chat": {"chatId": chat_id, "type": "group", "title": "Test Group"},
            "leftMembers": members,
            "removedBy": removed_by,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, LeftChatMembersEvent)
    return event
