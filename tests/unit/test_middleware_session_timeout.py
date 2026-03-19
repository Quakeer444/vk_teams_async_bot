"""Tests for SessionTimeoutMiddleware."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from vk_teams_async_bot.fsm.context import FSMContext
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage
from vk_teams_async_bot.middleware.session_timeout import SessionTimeoutMiddleware


@pytest.fixture
def storage() -> MemoryStorage:
    return MemoryStorage()


def _make_data(storage: MemoryStorage, key: tuple[str, str]) -> dict:
    return {"fsm_context": FSMContext(storage=storage, key=key)}


class TestTimestampUpdate:
    @pytest.mark.asyncio
    async def test_timestamp_updated_on_event(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=9999)
        handler = AsyncMock()
        key = ("chat1", "user1")

        await mw(handler, object(), _make_data(storage, key))

        assert key in mw._timestamps
        handler.assert_awaited_once()
        await mw.close()

    @pytest.mark.asyncio
    async def test_no_fsm_context_skips_timestamp(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=9999)
        handler = AsyncMock()

        await mw(handler, object(), {})

        assert len(mw._timestamps) == 0
        await mw.close()


class TestExpiredSessionCleanup:
    @pytest.mark.asyncio
    async def test_expired_session_cleared(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=1, check_interval=9999)
        key = ("chat1", "user1")
        await storage.set_state(key, "SomeState:active")
        mw._timestamps[key] = datetime.now() - timedelta(seconds=10)

        await mw._cleanup_expired()

        assert key not in mw._timestamps
        assert await storage.get_state(key) is None

    @pytest.mark.asyncio
    async def test_fresh_session_not_cleared(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=9999)
        key = ("chat1", "user1")
        await storage.set_state(key, "SomeState:active")
        mw._timestamps[key] = datetime.now()

        await mw._cleanup_expired()

        assert key in mw._timestamps
        assert await storage.get_state(key) == "SomeState:active"


class TestRaceCondition:
    @pytest.mark.asyncio
    async def test_refreshed_timestamp_not_cleared(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=1, check_interval=9999)
        key = ("chat1", "user1")
        await storage.set_state(key, "SomeState:active")
        mw._timestamps[key] = datetime.now() - timedelta(seconds=10)

        # Simulate refresh between expired list creation and pop
        mw._timestamps[key] = datetime.now()

        await mw._cleanup_expired()

        assert key in mw._timestamps
        assert await storage.get_state(key) == "SomeState:active"


class TestBackgroundTask:
    @pytest.mark.asyncio
    async def test_checker_task_started(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=9999)
        handler = AsyncMock()

        await mw(handler, object(), _make_data(storage, ("c", "u")))

        assert mw._task is not None
        assert not mw._task.done()
        await mw.close()

    @pytest.mark.asyncio
    async def test_close_cancels_task(self, storage: MemoryStorage):
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=9999)
        handler = AsyncMock()

        await mw(handler, object(), _make_data(storage, ("c", "u")))
        await mw.close()

        assert mw._task.done()


class TestOnTimeoutCallback:
    @pytest.mark.asyncio
    async def test_on_timeout_invoked(self, storage: MemoryStorage):
        calls: list[tuple[str, str]] = []

        async def on_timeout(chat_id: str, user_id: str) -> None:
            calls.append((chat_id, user_id))

        mw = SessionTimeoutMiddleware(
            storage,
            timeout=1,
            check_interval=9999,
            on_timeout=on_timeout,
        )
        key = ("chat1", "user1")
        await storage.set_state(key, "SomeState:active")
        mw._timestamps[key] = datetime.now() - timedelta(seconds=10)

        await mw._cleanup_expired()

        assert calls == [("chat1", "user1")]

    @pytest.mark.asyncio
    async def test_on_timeout_exception_does_not_propagate(
        self, storage: MemoryStorage
    ):
        async def bad_callback(chat_id: str, user_id: str) -> None:
            raise RuntimeError("callback error")

        mw = SessionTimeoutMiddleware(
            storage,
            timeout=1,
            check_interval=9999,
            on_timeout=bad_callback,
        )
        key = ("chat1", "user1")
        await storage.set_state(key, "SomeState:active")
        mw._timestamps[key] = datetime.now() - timedelta(seconds=10)

        await mw._cleanup_expired()  # should not raise
        assert key not in mw._timestamps


class TestCheckerLoopResilience:
    @pytest.mark.asyncio
    async def test_checker_loop_survives_cleanup_error(self, storage: MemoryStorage):
        """Checker loop should not die if cleanup raises."""
        mw = SessionTimeoutMiddleware(storage, timeout=300, check_interval=0.01)
        original_cleanup = mw._cleanup_expired
        call_count = 0

        async def failing_cleanup():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("storage error")
            await original_cleanup()

        mw._cleanup_expired = failing_cleanup
        mw._ensure_checker_running()
        await asyncio.sleep(0.05)
        assert call_count >= 2  # Loop survived the first error
        await mw.close()
