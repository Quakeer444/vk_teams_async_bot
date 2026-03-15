"""Building main and nested menus via inline keyboard buttons."""

import asyncio
import os

from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    CommandFilter,
    Dispatcher,
    InlineKeyboardMarkup,
    KeyboardButton,
    NewMessageEvent,
    StyleKeyboard,
)

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


def keyboard_start_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=2)
    keyboard.add(
        KeyboardButton(
            text="1 go first menu",
            callback_data="cb_first_menu",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(text="dev", callback_data="cb_dev"),
    )
    return keyboard


def keyboard_first_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=1)
    keyboard.add(
        KeyboardButton(
            text="2 go second menu",
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


def keyboard_second_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=1)
    keyboard.add(
        KeyboardButton(
            text="back to start menu",
            callback_data="cb_back_start_menu",
            style=StyleKeyboard.ATTENTION,
        ),
    )
    return keyboard


@dp.message(CommandFilter("start"))
async def start_menu_cmd(event: NewMessageEvent, bot: Bot):
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="hello",
        inline_keyboard_markup=keyboard_start_menu(),
    )


@dp.callback_query(CallbackDataFilter("cb_back_start_menu"))
async def start_menu_cb(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id)
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="you are back in the start menu",
        inline_keyboard_markup=keyboard_start_menu(),
    )


@dp.callback_query(CallbackDataFilter("cb_first_menu"))
async def first_menu(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id)
    await bot.edit_text(
        chat_id=event.chat.chat_id,
        msg_id=event.message.msg_id,
        text="you are in the first menu",
        inline_keyboard_markup=keyboard_first_menu(),
    )


@dp.callback_query(CallbackDataFilter("cb_second_menu"))
async def second_menu(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id)
    await bot.edit_text(
        chat_id=event.chat.chat_id,
        msg_id=event.message.msg_id,
        text="you are in the second menu",
        inline_keyboard_markup=keyboard_second_menu(),
    )


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
