"""E2E-specific fixtures.

bot, base_url, bot_token, test_user_id etc. are inherited from
tests/live/conftest.py automatically via pytest fixture discovery.
"""

import pytest

from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.fsm import MemoryStorage


@pytest.fixture
def storage() -> MemoryStorage:
    return MemoryStorage()


@pytest.fixture
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture
def dispatcher_with_storage(storage: MemoryStorage) -> Dispatcher:
    return Dispatcher(storage=storage)
