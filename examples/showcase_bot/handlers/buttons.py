from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
)

from ..keyboards import back_to_main_kb, buttons_showcase_kb


async def safe_edit(event: CallbackQueryEvent, bot: Bot, text: str, keyboard=None):
    await bot.answer_callback_query(query_id=event.query_id)
    if event.message:
        await bot.edit_text(
            chat_id=event.chat.chat_id,
            msg_id=event.message.msg_id,
            text=text,
            inline_keyboard_markup=keyboard,
        )
    else:
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=keyboard,
        )


def register_buttons_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:btn"))
    async def show_buttons(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Витрина кнопок\n\n"
            "Ниже представлены все 3 варианта StyleKeyboard, URL-кнопка "
            "и различные варианты компоновки (buttons_in_row)."
        )
        await safe_edit(event, bot, text, buttons_showcase_kb())

    @dp.callback_query(CallbackDataRegexpFilter(r"^btn:"))
    async def handle_button_click(event: CallbackQueryEvent, bot: Bot):
        style_name = event.callback_data.split(":", 1)[1]
        await bot.answer_callback_query(
            query_id=event.query_id,
            text=f"Вы нажали: {style_name}",
        )
