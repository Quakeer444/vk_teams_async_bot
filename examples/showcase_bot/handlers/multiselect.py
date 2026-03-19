from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
    FSMContext,
)

from ..keyboards import main_menu_kb, multiselect_confirm_kb, multiselect_kb
from ..states import MultiSelectStates


def _build_select_text(selected: set[str]) -> str:
    text = (
        "Выбор нескольких языков с пагинацией\n\n"
        "Отметьте нужные языки. Если список не помещается, переключайте страницы."
    )
    if selected:
        text += f"\nВыбрано: {', '.join(sorted(selected))}"
    return text


def register_multiselect_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:msel"))
    async def show_multiselect(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(MultiSelectStates.selecting)
        await fsm_context.update_data(selected=[], page=0)
        await bot.answer_callback_query(query_id=event.query_id)
        text = _build_select_text(set())
        kb = multiselect_kb(set(), page=0)
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=text,
                inline_keyboard_markup=kb,
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=text,
                inline_keyboard_markup=kb,
            )

    @dp.callback_query(CallbackDataRegexpFilter(r"^msel:page:"))
    async def change_page(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        page = int(event.callback_data.split(":", 2)[2])
        data = await fsm_context.get_data()
        selected = set(data.get("selected", []))
        await fsm_context.update_data(page=page)
        await bot.answer_callback_query(query_id=event.query_id)
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=_build_select_text(selected),
                inline_keyboard_markup=multiselect_kb(selected, page=page),
            )

    @dp.callback_query(CallbackDataFilter("msel:noop"))
    async def noop(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)

    @dp.callback_query(CallbackDataRegexpFilter(r"^msel:toggle:"))
    async def toggle_item(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        item = event.callback_data.split(":", 2)[2]
        data = await fsm_context.get_data()
        selected = set(data.get("selected", []))
        page = data.get("page", 0)
        if item in selected:
            selected.discard(item)
        else:
            selected.add(item)
        await fsm_context.update_data(selected=list(selected))
        await bot.answer_callback_query(query_id=event.query_id)
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=_build_select_text(selected),
                inline_keyboard_markup=multiselect_kb(selected, page=page),
            )

    @dp.callback_query(CallbackDataFilter("msel:clear"))
    async def clear_selection(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        data = await fsm_context.get_data()
        page = data.get("page", 0)
        await fsm_context.update_data(selected=[])
        await bot.answer_callback_query(query_id=event.query_id, text="Выбор очищен")
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=_build_select_text(set()),
                inline_keyboard_markup=multiselect_kb(set(), page=page),
            )

    @dp.callback_query(CallbackDataFilter("msel:next"))
    async def next_step(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        data = await fsm_context.get_data()
        selected = sorted(data.get("selected", []))
        langs = ", ".join(selected)
        await bot.answer_callback_query(query_id=event.query_id)
        text = f"Ваш выбор:\n{langs}"
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=text,
                inline_keyboard_markup=multiselect_confirm_kb(),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=text,
                inline_keyboard_markup=multiselect_confirm_kb(),
            )

    @dp.callback_query(CallbackDataFilter("msel:back"))
    async def back_to_select(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        data = await fsm_context.get_data()
        selected = set(data.get("selected", []))
        page = data.get("page", 0)
        await bot.answer_callback_query(query_id=event.query_id)
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=_build_select_text(selected),
                inline_keyboard_markup=multiselect_kb(selected, page=page),
            )

    @dp.callback_query(CallbackDataFilter("msel:confirm"))
    async def confirm_selection(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        data = await fsm_context.get_data()
        selected = sorted(data.get("selected", []))
        await fsm_context.clear()
        langs = ", ".join(selected)
        await bot.answer_callback_query(
            query_id=event.query_id, text="Выбор подтвержден!"
        )
        text = f"Выбранные языки: {langs}\n\nОтличный выбор!"
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=text,
                inline_keyboard_markup=main_menu_kb(),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=text,
                inline_keyboard_markup=main_menu_kb(),
            )
