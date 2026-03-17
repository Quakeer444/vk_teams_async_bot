import os

from vk_teams_async_bot import (
    APIError,
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
    FSMContext,
    NewMessageEvent,
    StateFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import back_to_main_kb
from ..keyboards_extra import chat_admin_menu_kb
from ..states import ChatAdminStates


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


def _admin_mode_enabled() -> bool:
    return os.environ.get("SHOWCASE_ADMIN_MODE") == "1"


def register_chat_admin_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:adm"))
    async def show_admin_menu(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Администрирование чата\n\n"
            "Чтение информации о чате работает в группах.\n"
            "Запись (название, описание, правила) требует "
            "SHOWCASE_ADMIN_MODE=1 и прав администратора.",
            chat_admin_menu_kb(),
        )

    # -- Read-only: get_chat_admins --
    @dp.callback_query(CallbackDataFilter("adm:admins"))
    async def show_admins(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            result = await bot.get_chat_admins(event.chat.chat_id)
            lines = [f"Администраторы чата ({len(result.admins)}):\n"]
            for admin in result.admins:
                role = "создатель" if admin.creator else "админ"
                lines.append(f"-- {admin.user_id} ({role})")
            text = "\n".join(lines)
        except APIError as e:
            text = f"Ошибка: {e.description}\n\n(Работает только в групповых чатах)"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )

    # -- Read-only: get_chat_members with cursor pagination --
    @dp.callback_query(CallbackDataFilter("adm:members"))
    async def show_members_first(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            result = await bot.get_chat_members(event.chat.chat_id)
            lines = [f"Участники чата ({len(result.members)}):\n"]
            for member in result.members:
                lines.append(f"-- {member.user_id}")
            text = "\n".join(lines)
            kb = chat_admin_menu_kb()
            if result.cursor:
                from vk_teams_async_bot import InlineKeyboardMarkup, KeyboardButton, StyleKeyboard
                kb = InlineKeyboardMarkup(buttons_in_row=1)
                kb.add(KeyboardButton(
                    text="Далее >>",
                    callback_data=f"adm:members:{result.cursor}",
                    style=StyleKeyboard.PRIMARY,
                ))
                kb.row(KeyboardButton(text="<< Назад", callback_data="menu:adm"))
        except APIError as e:
            text = f"Ошибка: {e.description}\n\n(Работает только в групповых чатах)"
            kb = chat_admin_menu_kb()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=kb,
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^adm:members:.+"))
    async def show_members_page(event: CallbackQueryEvent, bot: Bot):
        cursor = event.callback_data.split(":", 2)[2]
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            result = await bot.get_chat_members(event.chat.chat_id, cursor=cursor)
            lines = [f"Участники (продолжение, {len(result.members)}):\n"]
            for member in result.members:
                lines.append(f"-- {member.user_id}")
            text = "\n".join(lines)
            kb = chat_admin_menu_kb()
            if result.cursor:
                from vk_teams_async_bot import InlineKeyboardMarkup, KeyboardButton, StyleKeyboard
                kb = InlineKeyboardMarkup(buttons_in_row=1)
                kb.add(KeyboardButton(
                    text="Далее >>",
                    callback_data=f"adm:members:{result.cursor}",
                    style=StyleKeyboard.PRIMARY,
                ))
                kb.row(KeyboardButton(text="<< Назад", callback_data="menu:adm"))
        except APIError as e:
            text = f"Ошибка: {e.description}"
            kb = chat_admin_menu_kb()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=kb,
        )

    # -- Read-only: get_blocked_users --
    @dp.callback_query(CallbackDataFilter("adm:blocked"))
    async def show_blocked(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            result = await bot.get_blocked_users(event.chat.chat_id)
            if result.users:
                lines = [f"Заблокированные ({len(result.users)}):\n"]
                for user in result.users:
                    lines.append(f"-- {user.user_id}")
                text = "\n".join(lines)
            else:
                text = "Заблокированных пользователей нет."
        except APIError as e:
            text = f"Ошибка: {e.description}\n\n(Работает только в групповых чатах)"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )

    # -- Read-only: get_pending_users --
    @dp.callback_query(CallbackDataFilter("adm:pending"))
    async def show_pending(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            result = await bot.get_pending_users(event.chat.chat_id)
            if result.users:
                lines = [f"Ожидающие подтверждения ({len(result.users)}):\n"]
                for user in result.users:
                    lines.append(f"-- {user.user_id}")
                text = "\n".join(lines)
            else:
                text = "Ожидающих подтверждения нет."
        except APIError as e:
            text = f"Ошибка: {e.description}\n\n(Работает только в групповых чатах)"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )

    # -- Write: set_chat_title (gated) --
    @dp.callback_query(CallbackDataFilter("adm:title"))
    async def start_set_title(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        if not _admin_mode_enabled():
            await safe_edit(
                event, bot,
                "Изменение названия чата\n\n"
                "Для активации установите переменную окружения:\n"
                "SHOWCASE_ADMIN_MODE=1",
                chat_admin_menu_kb(),
            )
            return
        await fsm_context.set_state(ChatAdminStates.entering_title)
        await safe_edit(
            event, bot,
            "Введите новое название чата:",
            back_to_main_kb(),
        )

    @dp.message(StateFilter(ChatAdminStates.entering_title, storage))
    async def apply_title(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        try:
            await bot.set_chat_title(event.chat.chat_id, event.text or "")
            text = f"Название чата изменено на: {event.text}"
        except APIError as e:
            text = f"Ошибка: {e.description}"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )

    # -- Write: set_chat_about (gated) --
    @dp.callback_query(CallbackDataFilter("adm:about"))
    async def start_set_about(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        if not _admin_mode_enabled():
            await safe_edit(
                event, bot,
                "Изменение описания чата\n\n"
                "Для активации установите переменную окружения:\n"
                "SHOWCASE_ADMIN_MODE=1",
                chat_admin_menu_kb(),
            )
            return
        await fsm_context.set_state(ChatAdminStates.entering_about)
        await safe_edit(
            event, bot,
            "Введите новое описание чата:",
            back_to_main_kb(),
        )

    @dp.message(StateFilter(ChatAdminStates.entering_about, storage))
    async def apply_about(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        try:
            await bot.set_chat_about(event.chat.chat_id, event.text or "")
            text = f"Описание чата изменено."
        except APIError as e:
            text = f"Ошибка: {e.description}"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )

    # -- Write: set_chat_rules (gated) --
    @dp.callback_query(CallbackDataFilter("adm:rules"))
    async def start_set_rules(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        if not _admin_mode_enabled():
            await safe_edit(
                event, bot,
                "Изменение правил чата\n\n"
                "Для активации установите переменную окружения:\n"
                "SHOWCASE_ADMIN_MODE=1",
                chat_admin_menu_kb(),
            )
            return
        await fsm_context.set_state(ChatAdminStates.entering_rules)
        await safe_edit(
            event, bot,
            "Введите новые правила чата:",
            back_to_main_kb(),
        )

    @dp.message(StateFilter(ChatAdminStates.entering_rules, storage))
    async def apply_rules(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        try:
            await bot.set_chat_rules(event.chat.chat_id, event.text or "")
            text = f"Правила чата изменены."
        except APIError as e:
            text = f"Ошибка: {e.description}"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=chat_admin_menu_kb(),
        )
