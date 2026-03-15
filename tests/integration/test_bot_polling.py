"""Integration tests: bot polling loop lifecycle."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.errors import EventParsingError
from vk_teams_async_bot.handlers.message import MessageHandler
from vk_teams_async_bot.types.event import NewMessageEvent, RawUnknownEvent, parse_event


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

    @pytest.mark.asyncio
    async def test_shutdown_hooks_run_after_handler_drain(self):
        """Shutdown hooks must run after all handlers have finished."""
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        dp = Dispatcher()
        order = []

        handler_started = asyncio.Event()
        handler_proceed = asyncio.Event()

        @dp.message()
        async def slow_handler(event, b):
            handler_started.set()
            await handler_proceed.wait()
            order.append("handler_done")

        @bot.on_shutdown
        async def on_shutdown(b):
            order.append("shutdown_hook")

        events = [_make_event(event_id=1)]
        call_count = 0

        async def mock_get_events(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return events
            # Wait for handler to start, then stop polling
            await handler_started.wait()
            bot._running = False
            handler_proceed.set()
            return []

        bot.get_events = mock_get_events
        bot._running = True

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop.return_value = mock_loop_instance
            await bot.start_polling(dp)

        assert order == ["handler_done", "shutdown_hook"]


class TestUpdateLastEventId:
    def test_malformed_event_with_zero_id_does_not_reset_offset(self):
        """eventId=0 from a malformed event must not reset last_event_id."""
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        bot.last_event_id = 100

        malformed = RawUnknownEvent(eventId=0, type="unknown", payload={})
        bot._update_last_event_id(malformed)

        assert bot.last_event_id == 100

    def test_valid_event_updates_offset(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        bot.last_event_id = 50

        event = _make_event(event_id=51)
        bot._update_last_event_id(event)

        assert bot.last_event_id == 51

    def test_stale_event_id_does_not_regress_offset(self):
        bot = Bot(bot_token="test-token", url="https://test.example.com")
        bot.last_event_id = 100

        event = _make_event(event_id=99)
        bot._update_last_event_id(event)

        assert bot.last_event_id == 100
