import pytest

from vk_teams_async_bot.types.event import BaseEvent, RawUnknownEvent

pytestmark = pytest.mark.live


async def test_get_events_empty(bot):
    result = await bot.get_events(last_event_id=0, poll_time=1)
    assert isinstance(result, list)
    for event in result:
        assert isinstance(event, (BaseEvent, RawUnknownEvent))


async def test_get_events_after_send(bot, test_user_id):
    await bot.send_text(chat_id=test_user_id, text="live test: trigger event")
    result = await bot.get_events(last_event_id=0, poll_time=3)
    assert isinstance(result, list)
    assert len(result) > 0
