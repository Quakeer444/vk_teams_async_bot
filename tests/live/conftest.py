import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from dotenv import load_dotenv

from vk_teams_async_bot.bot import Bot

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env.test")
)


def _require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        pytest.skip(f"{key} not set in .env.test")
    return val


@pytest.fixture(scope="session")
def base_url() -> str:
    return _require_env("VK_TEAMS_BASE_URL")


@pytest.fixture(scope="session")
def bot_token() -> str:
    return _require_env("VK_TEAMS_BOT_TOKEN")


@pytest.fixture(scope="session")
def test_user_id() -> str:
    return _require_env("VK_TEAMS_TEST_USER_ID")


@pytest.fixture(scope="session")
def test_group_id() -> str:
    return _require_env("VK_TEAMS_TEST_GROUP_ID")


@pytest.fixture(scope="session")
def second_user_id() -> str:
    return _require_env("VK_TEAMS_TEST_SECOND_USER_ID")


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
async def bot(base_url: str, bot_token: str) -> AsyncGenerator[Bot, None]:
    b = Bot(bot_token=bot_token, url=base_url)
    yield b
    await b.close()
