import pytest

from vk_teams_async_bot.types.event import BaseEvent, RawUnknownEvent

pytestmark = pytest.mark.live


async def test_get_events_empty(bot):
    result = await bot.get_events(last_event_id=0, poll_time=1)
    assert isinstance(result, list)
    for event in result:
        assert isinstance(event, (BaseEvent, RawUnknownEvent))


@pytest.mark.xfail(reason="Bot may not receive its own messages via get_events")
async def test_get_events_after_send(bot, test_user_id):
    # Drain old events to get a fresh baseline
    drain = await bot.get_events(last_event_id=0, poll_time=1)
    fresh_id = max(e.event_id for e in drain) if drain else 0

    await bot.send_text(chat_id=test_user_id, text="live test: trigger event")
    result = await bot.get_events(last_event_id=fresh_id, poll_time=5)
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(e.event_id > fresh_id for e in result)
