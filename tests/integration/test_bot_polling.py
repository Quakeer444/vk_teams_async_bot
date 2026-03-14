"""Integration tests: bot polling loop lifecycle."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.errors import EventParsingError
from vk_teams_async_bot.handlers.message import MessageHandler
from vk_teams_async_bot.types.event import NewMessageEvent, parse_event


def _make_event(event_id: int = 1, text: str = "hi") -> NewMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "newMessage",
        "payload": {
            "msgId": "msg1",
            "chat": {"chatId": "chat1", "type": "private", "title": ""},
            "from": {"userId": "user1", "firstName": "Test"},
            "text": text,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, NewMessageEvent)
    return event


class TestPollingLoop:
    @pytest.mark.asyncio
    async def test_polling_loop_dispatches_events(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        dp = Dispatcher()
        handler_calls = []

        dp.add_handler(MessageHandler(callback=AsyncMock(side_effect=lambda e, b: handler_calls.append(e))))

        call_count = 0
        events = [_make_event(event_id=10), _make_event(event_id=20, text="second")]

        async def mock_get_events(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return events
            bot._running = False
            return []

        bot.get_events = mock_get_events
        bot._running = True
        await bot._polling_loop(dp)

        # Wait for background tasks to complete
        if bot._background_tasks:
            await asyncio.gather(*bot._background_tasks, return_exceptions=True)

        assert len(handler_calls) == 2
        assert bot.last_event_id == 20

    @pytest.mark.asyncio
    async def test_polling_loop_survives_event_parsing_error(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        dp = Dispatcher()

        call_count = 0

        async def mock_get_events(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise EventParsingError("bad event")
            bot._running = False
            return []

        bot.get_events = mock_get_events
        bot._running = True
        await bot._polling_loop(dp)

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_polling_loop_stops_when_running_false(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        dp = Dispatcher()

        call_count = 0

        async def mock_get_events(**kwargs):
            nonlocal call_count
            call_count += 1
            bot._running = False
            return []

        bot.get_events = mock_get_events
        bot._running = True
        await bot._polling_loop(dp)

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_startup_shutdown_hooks_called(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        dp = Dispatcher()
        hook_log = []

        @bot.on_startup
        async def startup(b):
            hook_log.append("startup")

        @bot.on_shutdown
        async def shutdown(b):
            hook_log.append("shutdown")

        async def mock_polling_loop(dispatcher):
            hook_log.append("polling")

        with patch.object(bot, "_polling_loop", side_effect=mock_polling_loop):
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop_instance = MagicMock()
                mock_loop.return_value = mock_loop_instance
                await bot.start_polling(dp)

        assert hook_log == ["startup", "polling", "shutdown"]
