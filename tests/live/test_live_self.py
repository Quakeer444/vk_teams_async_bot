import pytest

from vk_teams_async_bot.types.user import BotInfo, PhotoUrl

pytestmark = pytest.mark.live


async def test_get_self(bot):
    result = await bot.get_self()
    assert isinstance(result, BotInfo)
    assert isinstance(result.user_id, str)
    assert len(result.user_id) > 0
    assert result.nick is not None


async def test_get_self_all_fields(bot):
    result = await bot.get_self()
    assert isinstance(result, BotInfo)
    assert isinstance(result.user_id, str)
    assert len(result.user_id) > 0
    assert result.nick is not None
    assert isinstance(result.nick, str)
    assert result.first_name is not None
    assert isinstance(result.first_name, str)


async def test_get_self_photo_field(bot):
    result = await bot.get_self()
    assert isinstance(result, BotInfo)
    if result.photo is not None:
        assert isinstance(result.photo, list)
        for photo in result.photo:
            assert isinstance(photo, PhotoUrl)
            assert isinstance(photo.url, str)
            assert len(photo.url) > 0
