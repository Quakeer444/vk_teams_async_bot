from vk_teams_async_bot import (
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

from ..keyboards import (
    main_menu_kb,
    wzm_attendees_kb,
    wzm_confirm_kb,
    wzm_event_kb,
    wzm_meal_kb,
    wzm_notes_kb,
)
from ..states import WizardMixedStates


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


def register_wizard_mixed_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:wzm"))
    async def start_wizard(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardMixedStates.choosing_event)
        await fsm_context.set_data({})
        await safe_edit(
            event, bot,
            "Регистрация на событие -- Шаг 1/5\n\nВыберите тип события:",
            wzm_event_kb(),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^wzm:event:"))
    async def choose_event(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        event_type = event.callback_data.split(":")[2]
        await fsm_context.update_data(event_type=event_type)
        await fsm_context.set_state(WizardMixedStates.entering_attendees)
        await safe_edit(
            event, bot,
            f"Регистрация на событие -- Шаг 2/5\n\nСобытие: {event_type}\nВведите количество участников:",
            wzm_attendees_kb(),
        )

    @dp.message(StateFilter(WizardMixedStates.entering_attendees, storage))
    async def enter_attendees(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        text = (event.text or "").strip()
        try:
            count = int(text)
            if count <= 0:
                raise ValueError
        except ValueError:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text="Введите положительное число.",
                inline_keyboard_markup=wzm_attendees_kb(),
            )
            return
        await fsm_context.update_data(attendees=count)
        await fsm_context.set_state(WizardMixedStates.choosing_meal)
        data = await fsm_context.get_data()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f"Регистрация на событие -- Шаг 3/5\n\n"
                f"Событие: {data['event_type']}\n"
                f"Участники: {count}\n"
                f"Выберите тип питания:"
            ),
            inline_keyboard_markup=wzm_meal_kb(),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^wzm:meal:"))
    async def choose_meal(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        meal = event.callback_data.split(":")[2]
        await fsm_context.update_data(meal=meal)
        await fsm_context.set_state(WizardMixedStates.entering_notes)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            (
                f"Регистрация на событие -- Шаг 4/5\n\n"
                f"Событие: {data['event_type']}\n"
                f"Участники: {data['attendees']}\n"
                f"Питание: {meal}\n"
                f"Введите примечания (или нажмите Пропустить):"
            ),
            wzm_notes_kb(),
        )

    @dp.message(StateFilter(WizardMixedStates.entering_notes, storage))
    async def enter_notes(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        notes = (event.text or "").strip() or "(нет)"
        await fsm_context.update_data(notes=notes)
        await fsm_context.set_state(WizardMixedStates.confirm)
        data = await fsm_context.get_data()
        summary = (
            f"Регистрация на событие -- Шаг 5/5\n\n"
            f"Событие: {data['event_type']}\n"
            f"Участники: {data['attendees']}\n"
            f"Питание: {data['meal']}\n"
            f"Примечания: {notes}\n\n"
            f"Подтвердить регистрацию?"
        )
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=summary,
            inline_keyboard_markup=wzm_confirm_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzm:skip"))
    async def skip_notes(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.update_data(notes="(нет)")
        await fsm_context.set_state(WizardMixedStates.confirm)
        data = await fsm_context.get_data()
        summary = (
            f"Регистрация на событие -- Шаг 5/5\n\n"
            f"Событие: {data['event_type']}\n"
            f"Участники: {data['attendees']}\n"
            f"Питание: {data['meal']}\n"
            f"Примечания: (нет)\n\n"
            f"Подтвердить регистрацию?"
        )
        await safe_edit(event, bot, summary, wzm_confirm_kb())

    @dp.callback_query(CallbackDataFilter("wzm:confirm"))
    async def confirm_reg(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        data = await fsm_context.get_data()
        await fsm_context.clear()
        summary = (
            f"Регистрация подтверждена!\n\n"
            f"Событие: {data.get('event_type', '?')}\n"
            f"Участники: {data.get('attendees', '?')}\n"
            f"Питание: {data.get('meal', '?')}\n"
            f"Примечания: {data.get('notes', '(нет)')}"
        )
        await safe_edit(event, bot, summary, main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzm:cancel"))
    async def cancel_reg(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await safe_edit(event, bot, "Регистрация отменена.", main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzm:back:event"))
    async def back_to_event(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardMixedStates.choosing_event)
        await safe_edit(
            event, bot,
            "Регистрация на событие -- Шаг 1/5\n\nВыберите тип события:",
            wzm_event_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzm:back:attendees"))
    async def back_to_attendees(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardMixedStates.entering_attendees)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            f"Регистрация на событие -- Шаг 2/5\n\nСобытие: {data.get('event_type', '?')}\nВведите количество участников:",
            wzm_attendees_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzm:back:meal"))
    async def back_to_meal(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardMixedStates.choosing_meal)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            (
                f"Регистрация на событие -- Шаг 3/5\n\n"
                f"Событие: {data.get('event_type', '?')}\n"
                f"Участники: {data.get('attendees', '?')}\n"
                f"Выберите тип питания:"
            ),
            wzm_meal_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzm:back:notes"))
    async def back_to_notes(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(WizardMixedStates.entering_notes)
        data = await fsm_context.get_data()
        await safe_edit(
            event, bot,
            (
                f"Регистрация на событие -- Шаг 4/5\n\n"
                f"Событие: {data.get('event_type', '?')}\n"
                f"Участники: {data.get('attendees', '?')}\n"
                f"Питание: {data.get('meal', '?')}\n"
                f"Введите примечания (или нажмите Пропустить):"
            ),
            wzm_notes_kb(),
        )
