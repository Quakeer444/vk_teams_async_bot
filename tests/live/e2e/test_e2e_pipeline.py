"""E2E pipeline tests: dispatcher.feed_event + real Bot API calls."""

from __future__ import annotations

import pytest

from tests.helpers import make_callback_event, make_new_message_event
from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.filters.chat import ChatTypeFilter
from vk_teams_async_bot.filters.message import CommandFilter
from vk_teams_async_bot.types.enums import ChatType
from vk_teams_async_bot.types.event import CallbackQueryEvent, NewMessageEvent
from vk_teams_async_bot.types.response import MessageResponse

pytestmark = pytest.mark.live


async def test_command_handler_sends_reply(bot, test_user_id):
    """Handler receives /start via feed_event, calls real API, response valid."""
    dp = Dispatcher()
    result: dict = {}

    @dp.command("start")
    async def on_start(event, b):
        resp = await b.send_text(
            chat_id=test_user_id, text="E2E: command handler reply"
        )
        result["response"] = resp

    event = make_new_message_event(text="/start", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert "response" in result
    assert isinstance(result["response"], MessageResponse)
    assert result["response"].ok is True


async def test_message_handler_sends_reply(bot, test_user_id):
    """Generic message handler receives event, calls real API."""
    dp = Dispatcher()
    result: dict = {}

    @dp.message()
    async def on_message(event, b):
        resp = await b.send_text(
            chat_id=test_user_id, text="E2E: message handler reply"
        )
        result["response"] = resp

    event = make_new_message_event(text="hello", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert "response" in result
    assert result["response"].ok is True


async def test_command_handler_with_args(bot, test_user_id):
    """Handler for '/help topic' receives event with full text including args."""
    dp = Dispatcher()
    received_text: list[str] = []

    @dp.command("help")
    async def on_help(event, b):
        received_text.append(event.text)
        await b.send_text(chat_id=test_user_id, text="E2E: help handler")

    event = make_new_message_event(text="/help topic", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert len(received_text) == 1
    assert received_text[0] == "/help topic"
    parts = received_text[0].split()
    assert len(parts) == 2
    assert parts[1] == "topic"


async def test_callback_query_handler(bot, test_user_id):
    """CallbackQueryEvent routed to handler via feed_event."""
    dp = Dispatcher()
    received: list = []

    @dp.callback_query()
    async def on_callback(event, b):
        received.append(event)

    event = make_callback_event(callback_data="action:42", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert len(received) == 1
    assert isinstance(received[0], CallbackQueryEvent)
    assert received[0].callback_data == "action:42"


async def test_no_handler_matched(bot, test_user_id):
    """Event without a matching handler causes no crash."""
    dp = Dispatcher()

    @dp.command("start")
    async def on_start(event, b):
        pass

    event = make_new_message_event(text="not a command", chat_id=test_user_id)
    await dp.feed_event(event, bot)


async def test_chat_type_filter_routing(bot, test_user_id, test_group_id):
    """ChatTypeFilter routes private and group events to different handlers."""
    dp = Dispatcher()
    routed: list[str] = []

    @dp.message(ChatTypeFilter(ChatType.PRIVATE))
    async def on_private(event, b):
        routed.append("private")
        await b.send_text(chat_id=test_user_id, text="E2E: private reply")

    @dp.message(ChatTypeFilter(ChatType.GROUP))
    async def on_group(event, b):
        routed.append("group")
        await b.send_text(chat_id=test_group_id, text="E2E: group reply")

    private_event = make_new_message_event(
        text="hello", chat_id=test_user_id, chat_type="private"
    )
    group_event = make_new_message_event(
        text="hello", chat_id=test_group_id, chat_type="group"
    )

    await dp.feed_event(private_event, bot)
    await dp.feed_event(group_event, bot)

    assert routed == ["private", "group"]
