from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
    FSMContext,
)

from ..keyboards import DEFAULT_SETTINGS, SETTING_LABELS, toggle_settings_kb
from ..states import ToggleStates


def register_toggle_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:tgl"))
    async def show_toggles(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(ToggleStates.settings)
        data = await fsm_context.get_data()
        settings = data.get("settings", dict(DEFAULT_SETTINGS))
        await fsm_context.update_data(settings=settings)
        await bot.answer_callback_query(query_id=event.query_id)
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text="Настройки с переключателями\n\nНажмите на параметр, чтобы включить или выключить его.",
                inline_keyboard_markup=toggle_settings_kb(settings),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text="Настройки с переключателями\n\nНажмите на параметр, чтобы включить или выключить его.",
                inline_keyboard_markup=toggle_settings_kb(settings),
            )

    @dp.callback_query(CallbackDataRegexpFilter(r"^tgl:"))
    async def toggle_setting(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        setting_key = event.callback_data.split(":", 1)[1]
        if setting_key not in SETTING_LABELS:
            await bot.answer_callback_query(
                query_id=event.query_id, text="Неизвестная настройка"
            )
            return
        data = await fsm_context.get_data()
        settings = data.get("settings", dict(DEFAULT_SETTINGS))
        settings[setting_key] = not settings.get(setting_key, False)
        await fsm_context.update_data(settings=settings)
        label = SETTING_LABELS[setting_key]
        state = "ВКЛ" if settings[setting_key] else "ВЫКЛ"
        await bot.answer_callback_query(
            query_id=event.query_id,
            text=f"{label}: {state}",
        )
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text="Настройки с переключателями\n\nНажмите на параметр, чтобы включить или выключить его.",
                inline_keyboard_markup=toggle_settings_kb(settings),
            )
