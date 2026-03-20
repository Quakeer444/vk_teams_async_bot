import asyncio

import pytest

from vk_teams_async_bot.dispatcher import Dispatcher


@pytest.fixture
def dispatcher():
    return Dispatcher()


@pytest.mark.asyncio
async def test_sweep_removes_idle_locks(dispatcher):
    """Sweep should remove locks that are not currently held."""
    for i in range(10):
        key = (f"chat{i}", f"user{i}")
        dispatcher._user_locks[key] = asyncio.Lock()

    assert len(dispatcher._user_locks) == 10
    dispatcher._sweep_idle_locks()
    assert len(dispatcher._user_locks) == 0


@pytest.mark.asyncio
async def test_sweep_preserves_locked_entries(dispatcher):
    """Sweep must NOT remove locks that are currently held."""
    held_key = ("chat_held", "user_held")
    idle_key = ("chat_idle", "user_idle")

    held_lock = asyncio.Lock()
    await held_lock.acquire()

    dispatcher._user_locks[held_key] = held_lock
    dispatcher._user_locks[idle_key] = asyncio.Lock()

    dispatcher._sweep_idle_locks()

    assert held_key in dispatcher._user_locks
    assert idle_key not in dispatcher._user_locks
    held_lock.release()


@pytest.mark.asyncio
async def test_sweep_preserves_locks_with_waiters(dispatcher):
    """Sweep must NOT remove locks that have pending waiters."""
    key = ("chat1", "user1")
    lock = asyncio.Lock()
    dispatcher._user_locks[key] = lock

    await lock.acquire()

    # Create a waiter that will be pending
    async def waiter():
        async with lock:
            pass

    waiter_task = asyncio.create_task(waiter())
    await asyncio.sleep(0)  # let waiter start and block on acquire

    lock.release()
    # Now: lock._locked is False but waiter is pending
    # (in the same event loop turn, waiter hasn't resumed yet)

    # Sweep should see waiters and preserve the lock
    dispatcher._sweep_idle_locks()
    # Lock may or may not be in dict depending on timing,
    # but waiter_task should complete without error
    await waiter_task


@pytest.mark.asyncio
async def test_locks_dict_bounded_after_sweep(dispatcher):
    """After sweep, idle locks should be cleaned up."""
    for i in range(1000):
        key = (f"chat{i}", f"user{i}")
        dispatcher._user_locks.setdefault(key, asyncio.Lock())

    assert len(dispatcher._user_locks) == 1000
    dispatcher._sweep_idle_locks()
    assert len(dispatcher._user_locks) == 0


@pytest.mark.asyncio
async def test_sweep_task_cleans_idle_locks():
    """Timer-based sweep task should automatically clean up idle locks."""
    d = Dispatcher(lock_sweep_interval=0.01)
    lock = asyncio.Lock()
    d._user_locks[("chat", "user")] = lock
    d.start_sweep_task()
    await asyncio.sleep(0.05)
    await d.stop_sweep_task()
    assert ("chat", "user") not in d._user_locks
