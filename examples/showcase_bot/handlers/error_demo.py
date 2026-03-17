from vk_teams_async_bot import (
    APIError,
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    Dispatcher,
)

from ..keyboards_extra import error_demo_menu_kb


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


def register_error_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:err"))
    async def show_error_menu(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Обработка ошибок\n\n"
            "Демонстрация перехвата и обработки ошибок API.\n"
            "Выберите сценарий:",
            error_demo_menu_kb(),
        )

    # Demo 1: APIError -- edit nonexistent message
    @dp.callback_query(CallbackDataFilter("err:api"))
    async def demo_api_error(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id="nonexistent_msg_id_12345",
                text="test",
            )
            result = "Ошибка не возникла (неожиданно)"
        except APIError as e:
            result = (
                f"APIError перехвачена!\n\n"
                f"status_code: {e.status_code}\n"
                f"description: {e.description}"
            )
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Демо: edit_text с несуществующим msg_id\n\n{result}",
            inline_keyboard_markup=error_demo_menu_kb(),
        )

    # Demo 2: Error hierarchy display
    @dp.callback_query(CallbackDataFilter("err:hierarchy"))
    async def demo_hierarchy(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Иерархия ошибок библиотеки\n\n"
            "VKTeamsError (базовый)\n"
            "  |-- APIError (status_code, description)\n"
            "  |     |-- ServerError (5xx)\n"
            "  |     |-- RateLimitError (429)\n"
            "  |-- NetworkError (проблемы сети)\n"
            "  |-- TimeoutError (таймаут запроса)\n"
            "  |-- SessionError (ошибка сессии)\n"
            "  |-- PollingError (ошибка polling)\n"
            "  |-- EventParsingError (парсинг событий)\n\n"
            "Все ошибки наследуют от VKTeamsError, "
            "поэтому except VKTeamsError перехватит любую."
        )
        await safe_edit(event, bot, text, error_demo_menu_kb())

    # Demo 3: Safe try/except pattern
    @dp.callback_query(CallbackDataFilter("err:safe"))
    async def demo_safe_pattern(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            await bot.get_file_info("nonexistent_file_id_12345")
            result = "Файл найден (неожиданно)"
        except APIError as e:
            result = (
                f"Безопасный перехват:\n"
                f"APIError {e.status_code}: {e.description}\n\n"
                f"Бот продолжает работу. Пользователь видит "
                f"понятное сообщение вместо падения."
            )
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Демо: get_file_info с несуществующим file_id\n\n{result}",
            inline_keyboard_markup=error_demo_menu_kb(),
        )
