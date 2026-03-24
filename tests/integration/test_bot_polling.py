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

        dp.add_handler(
            MessageHandler(
                callback=AsyncMock(side_effect=lambda e, b: handler_calls.append(e))
            )
        )

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


class TestDrainTasks:
    @pytest.mark.asyncio
    async def test_drain_awaits_pending_tasks(self):
        bot = Bot(bot_token="test-token")
        finished = []

        async def work():
            await asyncio.sleep(0)
            finished.append(1)

        task = asyncio.create_task(work())
        bot._background_tasks.add(task)

        await bot._drain_tasks()

        assert len(finished) == 1
        assert len(bot._background_tasks) == 0

    @pytest.mark.asyncio
    async def test_drain_timeout_cancels_remaining_tasks(self):
        bot = Bot(bot_token="test-token", shutdown_timeout=0.01)

        async def never_ends():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                raise

        task = asyncio.create_task(never_ends())
        bot._background_tasks.add(task)

        await bot._drain_tasks()

        assert task.cancelled()
        assert len(bot._background_tasks) == 0


class TestStartPollingEdgeCases:
    @pytest.mark.asyncio
    async def test_signal_not_implemented_is_handled(self):
        """NotImplementedError from add_signal_handler is caught and logged."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()

        # Block start_sweep_task so stop_sweep_task has nothing to await,
        # avoiding an async context switch that confuses coverage.py on Python 3.11.
        with patch.object(dp, "start_sweep_task"):
            with patch.object(bot, "_polling_loop", new_callable=AsyncMock):
                with patch("asyncio.get_running_loop") as mock_get_loop:
                    mock_loop = MagicMock()
                    mock_loop.add_signal_handler.side_effect = NotImplementedError
                    mock_get_loop.return_value = mock_loop
                    await bot.start_polling(dp)  # must not raise

    @pytest.mark.asyncio
    async def test_finally_calls_stop_sweep_and_drain(self):
        """stop_sweep_task and _drain_tasks are called in the finally block."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()
        calls = []

        original_stop = dp.stop_sweep_task

        async def patched_stop():
            calls.append("stop_sweep")
            await original_stop()

        dp.stop_sweep_task = patched_stop

        original_drain = bot._drain_tasks

        async def patched_drain():
            calls.append("drain")
            await original_drain()

        bot._drain_tasks = patched_drain

        # Block start_sweep_task so stop_sweep_task returns immediately
        # (no pending task to await), preventing an async context switch
        # that breaks coverage tracing in Python 3.11 finally blocks.
        with patch.object(dp, "start_sweep_task"):
            with patch.object(bot, "_polling_loop", new_callable=AsyncMock):
                await bot.start_polling(dp)

        assert "stop_sweep" in calls
        assert "drain" in calls

    @pytest.mark.asyncio
    async def test_shutdown_hook_is_called(self):
        """Shutdown hooks run after polling stops."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()
        called = []

        @bot.on_shutdown
        async def hook(b):
            called.append(True)

        with patch.object(dp, "start_sweep_task"):
            with patch.object(bot, "_polling_loop", new_callable=AsyncMock):
                await bot.start_polling(dp)

        assert called == [True]

    @pytest.mark.asyncio
    async def test_shutdown_hook_exception_is_swallowed(self):
        """An exception inside a shutdown hook must not propagate."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()

        @bot.on_shutdown
        async def bad_hook(b):
            raise RuntimeError("hook failure")

        with patch.object(dp, "start_sweep_task"):
            with patch.object(bot, "_polling_loop", new_callable=AsyncMock):
                await bot.start_polling(dp)  # must not raise


class TestPollingLoopEdgeCases:
    @pytest.mark.asyncio
    async def test_exception_breaks_loop_when_already_stopped(self):
        """Line 238: if not self._running: break inside exception handler."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()

        async def mock_get_events(**kwargs):
            bot._running = False
            raise RuntimeError("error while stopping")

        bot.get_events = mock_get_events
        bot._running = True
        await bot._polling_loop(dp)  # must exit without sleeping

    @pytest.mark.asyncio
    async def test_task_done_discards_task_with_unhandled_exception(self):
        """_task_done logs and discards a task that raised an exception."""
        bot = Bot(bot_token="test-token")

        async def failing():
            raise ValueError("task error")

        task = asyncio.create_task(failing())
        bot._background_tasks.add(task)
        task.add_done_callback(bot._task_done)

        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert task not in bot._background_tasks

    @pytest.mark.asyncio
    async def test_safe_dispatch_swallows_feed_event_exception(self):
        """_safe_dispatch catches exceptions from dispatcher.feed_event."""
        bot = Bot(bot_token="test-token")
        dp = Dispatcher()
        event = _make_event(event_id=1)

        with patch.object(dp, "feed_event", side_effect=RuntimeError("dispatch error")):
            await bot._safe_dispatch(dp, event)  # must not raise


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
