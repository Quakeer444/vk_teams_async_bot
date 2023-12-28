"""
Составление основного и вложенных меню через Inline кнопки
"""

import asyncio

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.constants import StyleKeyboard
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.filter import Filter
from vk_teams_async_bot.handler import BotButtonCommandHandler, CommandHandler
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton

app = Bot(bot_token="TOKEN", url="URL")


def keyboad_start_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=2)
    keyboard.add(
        KeyboardButton(
            text="1️⃣ go first menu",
            callback_data="cb_first_menu",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(text="🕹 dev", callback_data="cb_dev"),
    )
    return keyboard


def keyboad_first_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=1)
    keyboard.add(
        KeyboardButton(
            text="2️⃣ go second menu",
            callback_data="cb_second_menu",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="back to start menu",
            callback_data="cb_back_start_menu",
            style=StyleKeyboard.ATTENTION,
        ),
    )
    return keyboard


def keyboad_second_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=1)
    keyboard.add(
        KeyboardButton(
            text="back to start menu",
            callback_data="cb_back_start_menu",
            style=StyleKeyboard.ATTENTION,
        ),
    )
    return keyboard


async def start_menu(event: Event, bot: Bot):
    if hasattr(event, "callbackData"):
        await bot.answer_callback_query(query_id=event.queryId)
    text = "hello" if event.text else "you are back in the start menu"
    await bot.send_text(
        chat_id=event.chat.chatId,
        text=text,
        inline_keyboard_markup=keyboad_start_menu(),
    )


async def first_menu(event: Event, bot: Bot):
    await bot.answer_callback_query(query_id=event.queryId)
    await bot.edit_text(
        chat_id=event.chat.chatId,
        msg_id=event.cb_message.msgId,
        text="you are in the first menu",
        inline_keyboard_markup=keyboad_first_menu(),
    )


async def second_menu(event: Event, bot: Bot):
    await bot.edit_text(
        chat_id=event.chat.chatId,
        msg_id=event.cb_message.msgId,
        text="you are in the second menu",
        inline_keyboard_markup=keyboad_second_menu(),
    )


app.dispatcher.add_handler(
    CommandHandler(callback=start_menu, filters=Filter.command("/start")),
)

app.dispatcher.add_handler(
    BotButtonCommandHandler(
        callback=first_menu, filters=Filter.callback_data("cb_first_menu")
    )
)

app.dispatcher.add_handler(
    BotButtonCommandHandler(
        callback=second_menu, filters=Filter.callback_data("cb_second_menu")
    )
)

app.dispatcher.add_handler(
    BotButtonCommandHandler(
        callback=start_menu, filters=Filter.callback_data("cb_back_start_menu")
    )
)


async def main():
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
