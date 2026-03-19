"""Integration tests: long-poll handling (empty/non-empty events)."""

import re

import pytest

try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses required", allow_module_level=True)

from vk_teams_async_bot.client.retry import RetryPolicy
from vk_teams_async_bot.client.session import VKTeamsSession
from vk_teams_async_bot.methods.events import EventMethods
from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    NewMessageEvent,
    RawUnknownEvent,
)

BASE_URL = "https://api.test.example.com"
BASE_PATH = "/bot/v1"
TOKEN = "test-token"

EVENTS_GET = re.compile(r".*/bot/v1/events/get")


class FakeEventClient(EventMethods):
    def __init__(self, session):
        self._session = session


def _make_session() -> VKTeamsSession:
    return VKTeamsSession(
        BASE_URL,
        BASE_PATH,
        TOKEN,
        timeout=5,
        retry_policy=RetryPolicy(max_retries=0),
    )


class TestLongPoll:
    @pytest.mark.asyncio
    async def test_empty_events_returns_empty_list(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(EVENTS_GET, payload={"ok": True, "events": []})
                client = FakeEventClient(session)
                events = await client.get_events(last_event_id=0, poll_time=1)
                assert events == []

    @pytest.mark.asyncio
    async def test_non_empty_events_parsed(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(
                    EVENTS_GET,
                    payload={
                        "ok": True,
                        "events": [
                            {
                                "eventId": 1,
                                "type": "newMessage",
                                "payload": {
                                    "msgId": "msg1",
                                    "chat": {
                                        "chatId": "chat1",
                                        "type": "private",
                                        "title": "",
                                    },
                                    "from": {"userId": "user1", "firstName": "Test"},
                                    "text": "hello",
                                    "timestamp": 1234567890,
                                },
                            },
                        ],
                    },
                )
                client = FakeEventClient(session)
                events = await client.get_events(last_event_id=0, poll_time=1)
                assert len(events) == 1
                assert isinstance(events[0], NewMessageEvent)
                assert events[0].text == "hello"
                assert events[0].msg_id == "msg1"

    @pytest.mark.asyncio
    async def test_unknown_event_type_returns_raw(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(
                    EVENTS_GET,
                    payload={
                        "ok": True,
                        "events": [
                            {
                                "eventId": 2,
                                "type": "changedChatInfo",
                                "payload": {"chatId": "chat1"},
                            },
                        ],
                    },
                )
                client = FakeEventClient(session)
                events = await client.get_events(last_event_id=0, poll_time=1)
                assert len(events) == 1
                assert isinstance(events[0], RawUnknownEvent)
                assert events[0].type == "changedChatInfo"

    @pytest.mark.asyncio
    async def test_multiple_events_mixed(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(
                    EVENTS_GET,
                    payload={
                        "ok": True,
                        "events": [
                            {
                                "eventId": 1,
                                "type": "newMessage",
                                "payload": {
                                    "msgId": "m1",
                                    "chat": {
                                        "chatId": "c1",
                                        "type": "private",
                                        "title": "",
                                    },
                                    "from": {"userId": "u1", "firstName": "A"},
                                    "text": "hi",
                                    "timestamp": 100,
                                },
                            },
                            {
                                "eventId": 2,
                                "type": "unknownType",
                                "payload": {"data": "x"},
                            },
                            {
                                "eventId": 3,
                                "type": "callbackQuery",
                                "payload": {
                                    "chat": {
                                        "chatId": "c1",
                                        "type": "private",
                                        "title": "",
                                    },
                                    "from": {"userId": "u1", "firstName": "A"},
                                    "queryId": "q1",
                                    "callbackData": "btn1",
                                },
                            },
                        ],
                    },
                )
                client = FakeEventClient(session)
                events = await client.get_events(last_event_id=0, poll_time=1)
                assert len(events) == 3
                assert isinstance(events[0], NewMessageEvent)
                assert isinstance(events[1], RawUnknownEvent)
                assert isinstance(events[2], CallbackQueryEvent)
