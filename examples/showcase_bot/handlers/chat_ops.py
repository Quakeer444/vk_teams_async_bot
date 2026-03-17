from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    ChatAction,
    ChatInfoChannel,
    ChatInfoGroup,
    ChatInfoPrivate,
    Dispatcher,
    InlineKeyboardMarkup,
    KeyboardButton,
)

from ..keyboards import chat_ops_menu_kb
from .utils import safe_edit


def register_chat_ops_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:chat"))
    async def show_chat_ops(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Действия в чате\n\nВыберите, что хотите проверить:",
            chat_ops_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("chat:info"))
    async def chat_info(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        info = await bot.get_chat_info(chat_id)

        lines = ["Информация о чате", ""]
        if isinstance(info, ChatInfoPrivate):
            lines.extend([
                f"Тип: личный",
                f"Имя: {info.first_name or ''} {info.last_name or ''}".strip(),
                f"Ник: {info.nick or '(нет)'}",
                f"О себе: {info.about or '(нет)'}",
                f"Бот: {info.is_bot}",
            ])
        elif isinstance(info, ChatInfoGroup):
            lines.extend([
                f"Тип: группа",
                f"Название: {info.title or '(нет)'}",
                f"Описание: {info.about or '(нет)'}",
                f"Правила: {info.rules or '(нет)'}",
                f"Публичный: {info.public}",
            ])
        elif isinstance(info, ChatInfoChannel):
            lines.extend([
                f"Тип: канал",
                f"Название: {info.title or '(нет)'}",
                f"Описание: {info.about or '(нет)'}",
                f"Правила: {info.rules or '(нет)'}",
                f"Публичный: {info.public}",
            ])

        await bot.send_text(
            chat_id=chat_id,
            text="\n".join(lines),
            inline_keyboard_markup=chat_ops_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("chat:typing"))
    async def show_typing(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id, text="Показываю печатание...")
        chat_id = event.chat.chat_id
        await bot.send_chat_actions(chat_id, actions=[ChatAction.TYPING])
        await bot.send_text(
            chat_id=chat_id,
            text="Действие TYPING отправлено. Видно ~10 секунд или до отправки сообщения ботом.",
            inline_keyboard_markup=chat_ops_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("chat:looking"))
    async def show_looking(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id, text="Показываю просмотр...")
        chat_id = event.chat.chat_id
        await bot.send_chat_actions(chat_id, actions=[ChatAction.LOOKING])
        await bot.send_text(
            chat_id=chat_id,
            text="Действие LOOKING отправлено. Видно ~10 секунд или до отправки сообщения ботом.",
            inline_keyboard_markup=chat_ops_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("chat:pin"))
    async def pin_demo(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        msg = await bot.send_text(chat_id, "Это сообщение будет закреплено")
        await bot.pin_message(chat_id, msg.msg_id)

        unpin_kb = InlineKeyboardMarkup(buttons_in_row=1)
        unpin_kb.add(KeyboardButton(text="Открепить", callback_data=f"chat:unpin:{msg.msg_id}"))
        unpin_kb.add(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
        await bot.send_text(
            chat_id=chat_id,
            text="Сообщение закреплено! Нажмите, чтобы открепить.",
            inline_keyboard_markup=unpin_kb,
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^chat:unpin:"))
    async def unpin_demo(event: CallbackQueryEvent, bot: Bot):
        msg_id = event.callback_data.split(":")[2]
        await bot.answer_callback_query(query_id=event.query_id)
        chat_id = event.chat.chat_id
        await bot.unpin_message(chat_id, msg_id)
        await bot.send_text(
            chat_id=chat_id,
            text="Сообщение откреплено.",
            inline_keyboard_markup=chat_ops_menu_kb(),
        )
