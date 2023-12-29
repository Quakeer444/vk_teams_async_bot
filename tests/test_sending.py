import asyncio

import pytest

from vk_teams_async_bot.bot import Bot
from local_.config import env
from vk_teams_async_bot.constants import StyleKeyboard, ParseMode
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton

test_bot = Bot(bot_token=env.TEST_BOT_TOKEN.get_secret_value())


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_keyboad_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=1)
    keyboard.row(
        KeyboardButton(
            text="🛠 first button", callback_data="cb_one", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="🕹 second button", callback_data="cb_two", style=StyleKeyboard.BASE
        ),
        KeyboardButton(
            text="🕹 third button", callback_data="cb_three", style=StyleKeyboard.ATTENTION
        ),
    )
    return keyboard


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chat_id, text, parse_mode",
    [
        (env.TEST_USER_ID, 'test message', None),
        (env.TEST_USER_ID, '*test message*', ParseMode.MARKDOWNV2),
        (env.TEST_USER_ID, '<b>test message</b>', ParseMode.HTML),

        (env.TEST_GROUP_ID, 'test message', None),
        (env.TEST_GROUP_ID, '*test message*', ParseMode.MARKDOWNV2),
        (env.TEST_GROUP_ID, '<b>test message</b>', ParseMode.HTML),
    ]
)
class TestMessageFormat:
    async def test_send_message_text(self, chat_id: str, text: str, parse_mode: str | None):
        response = await test_bot.send_text(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        print(response)
        assert response.get("msgId").isdigit()
        assert response.get("ok") is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chat_id,",
    [
        env.TEST_USER_ID,
        env.TEST_GROUP_ID
    ]
)
class TestMessageKeyboard:
    async def test_send_message_with_keyboard(self, chat_id: str, test_keyboad_menu):
        response = await test_bot.send_text(
            chat_id=chat_id,
            text="test message with inline keyboard",
            inline_keyboard_markup=test_keyboad_menu
        )
        print(response)
        assert response.get("msgId").isdigit()
        assert response.get("ok") is True
