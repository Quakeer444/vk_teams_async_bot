import pytest

from vk_teams_async_bot.types.user import BotInfo

pytestmark = pytest.mark.live


async def test_get_self(bot):
    result = await bot.get_self()
    assert isinstance(result, BotInfo)
    assert isinstance(result.user_id, str)
    assert len(result.user_id) > 0
    assert result.nick is not None
