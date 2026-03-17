import asyncio

from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    Dispatcher,
)

from ..keyboards import back_to_main_kb, messages_menu_kb
from .utils import safe_edit


def register_messages_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:msg"))
    async def show_messages(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Действия с сообщениями\n\nВыберите, что хотите показать на примере:",
            messages_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("msg:reply"))
    async def demo_reply(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        original = await bot.send_text(chat_id, "Исходное сообщение")
        await bot.send_text(
            chat_id,
            "Это ответ на сообщение выше",
            reply_msg_id=original.msg_id,
            inline_keyboard_markup=messages_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("msg:forward"))
    async def demo_forward(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        original = await bot.send_text(chat_id, "Это сообщение будет переслано ниже")
        await bot.send_text(
            chat_id,
            "Переслано:",
            forward_chat_id=chat_id,
            forward_msg_id=original.msg_id,
            inline_keyboard_markup=messages_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("msg:edit"))
    async def demo_edit(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        msg = await bot.send_text(chat_id, "До редактирования -- подождите 1 секунду...")
        await asyncio.sleep(1)
        await bot.edit_text(
            chat_id,
            msg.msg_id,
            "После редактирования -- сообщение обновлено!",
            inline_keyboard_markup=messages_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("msg:delete"))
    async def demo_delete(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        msg = await bot.send_text(chat_id, "Это сообщение самоуничтожится через 1 секунду...")
        await asyncio.sleep(1)
        await bot.delete_messages(chat_id, msg.msg_id)
        await bot.send_text(
            chat_id,
            "Сообщение успешно удалено",
            inline_keyboard_markup=messages_menu_kb(),
        )
