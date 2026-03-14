import re

from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    Dispatcher,
    FSMContext,
    NewMessageEvent,
    StateFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import main_menu_kb, wzt_back_cancel_kb, wzt_confirm_kb
from ..states import WizardTextStates

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")
PHONE_RE = re.compile(r"^\d{10,15}$")


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


def register_wizard_text_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:wzt"))
    async def start_wizard(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardTextStates.entering_name)
        await fsm_context.set_data({})
        await safe_edit(
            event, bot,
            "Регистрация -- Шаг 1/3\n\nВведите ваше полное имя (имя и фамилия):",
            wzt_back_cancel_kb(),
        )

    @dp.message(StateFilter(WizardTextStates.entering_name, storage))
    async def enter_name(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        name = (event.text or "").strip()
        if len(name.split()) < 2:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text="Введите минимум имя и фамилию (2+ слова).",
                inline_keyboard_markup=wzt_back_cancel_kb(),
            )
            return
        await fsm_context.update_data(name=name)
        await fsm_context.set_state(WizardTextStates.entering_email)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Регистрация -- Шаг 2/3\n\nИмя: {name}\nВведите email:",
            inline_keyboard_markup=wzt_back_cancel_kb(back_step="name"),
        )

    @dp.message(StateFilter(WizardTextStates.entering_email, storage))
    async def enter_email(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        email = (event.text or "").strip()
        if not EMAIL_RE.match(email):
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text="Неверный формат email. Попробуйте снова.",
                inline_keyboard_markup=wzt_back_cancel_kb(back_step="name"),
            )
            return
        await fsm_context.update_data(email=email)
        await fsm_context.set_state(WizardTextStates.entering_phone)
        data = await fsm_context.get_data()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Регистрация -- Шаг 3/3\n\nИмя: {data['name']}\nEmail: {email}\nВведите телефон (10-15 цифр):",
            inline_keyboard_markup=wzt_back_cancel_kb(back_step="email"),
        )

    @dp.message(StateFilter(WizardTextStates.entering_phone, storage))
    async def enter_phone(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        phone = (event.text or "").strip()
        if not PHONE_RE.match(phone):
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text="Неверный телефон. Введите только 10-15 цифр.",
                inline_keyboard_markup=wzt_back_cancel_kb(back_step="email"),
            )
            return
        await fsm_context.update_data(phone=phone)
        await fsm_context.set_state(WizardTextStates.confirm)
        data = await fsm_context.get_data()
        summary = (
            f"Регистрация -- Подтверждение\n\n"
            f"Имя: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Телефон: {phone}\n\n"
            f"Все верно?"
        )
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=summary,
            inline_keyboard_markup=wzt_confirm_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzt:confirm"))
    async def confirm_reg(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        data = await fsm_context.get_data()
        await fsm_context.clear()
        summary = (
            f"Регистрация завершена!\n\n"
            f"Имя: {data.get('name', '?')}\n"
            f"Email: {data.get('email', '?')}\n"
            f"Телефон: {data.get('phone', '?')}"
        )
        await safe_edit(event, bot, summary, main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzt:cancel"))
    async def cancel_reg(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await safe_edit(event, bot, "Регистрация отменена.", main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzt:back:name"))
    async def back_to_name(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardTextStates.entering_name)
        await safe_edit(
            event, bot,
            "Регистрация -- Шаг 1/3\n\nВведите ваше полное имя:",
            wzt_back_cancel_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzt:back:email"))
    async def back_to_email(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardTextStates.entering_email)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            f"Регистрация -- Шаг 2/3\n\nИмя: {data.get('name', '?')}\nВведите email:",
            wzt_back_cancel_kb(back_step="name"),
        )

    @dp.callback_query(CallbackDataFilter("wzt:back:phone"))
    async def back_to_phone(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardTextStates.entering_phone)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            f"Регистрация -- Шаг 3/3\n\nИмя: {data.get('name', '?')}\nEmail: {data.get('email', '?')}\nВведите телефон:",
            wzt_back_cancel_kb(back_step="email"),
        )
