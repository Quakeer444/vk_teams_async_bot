from vk_teams_async_bot import Bot, CallbackDataFilter, CallbackQueryEvent, Dispatcher

from ..keyboards import category_framework_kb
from .utils import safe_edit


def register_framework_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("fw:botinfo"))
    async def bot_info(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        info = await bot.get_self()
        lines = [
            "Информация о боте",
            "",
            f"User ID: {info.user_id}",
            f"Ник: {info.nick or '(нет)'}",
            f"Имя: {info.first_name or '(нет)'}",
            f"О боте: {info.about or '(нет)'}",
        ]
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="\n".join(lines),
            inline_keyboard_markup=category_framework_kb(),
        )

    @dp.callback_query(CallbackDataFilter("fw:middleware"))
    async def show_middleware(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Middleware\n\n"
            "Middleware оборачивает каждый вызов обработчика. "
            "В этом боте используются:\n\n"
            "1. LoggingMiddleware -- логирует все события с временем обработки\n"
            "2. SessionTimeoutMiddleware -- автоматически очищает состояние "
            "пользователя после 10 минут неактивности\n\n"
            "Пример:\n"
            "class LoggingMiddleware(BaseMiddleware):\n"
            "    async def __call__(self, handler, event, data):\n"
            "        start = time.monotonic()\n"
            "        result = await handler(event, data)\n"
            "        elapsed = time.monotonic() - start\n"
            '        logger.info("Processed in %.1fms", elapsed * 1000)\n'
            "        return result"
        )
        await safe_edit(event, bot, text, category_framework_kb())

    @dp.callback_query(CallbackDataFilter("fw:lifecycle"))
    async def show_lifecycle(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Lifecycle (startup/shutdown)\n\n"
            "Хуки жизненного цикла бота:\n\n"
            "@bot.on_startup\n"
            "async def startup(bot: Bot):\n"
            "    info = await bot.get_self()\n"
            '    logger.info("Bot started: %s", info.nick)\n\n'
            "@bot.on_shutdown\n"
            "async def shutdown(bot: Bot):\n"
            "    await cleanup_resources()\n"
            '    logger.info("Bot stopped")\n\n'
            "startup вызывается перед началом polling.\n"
            "shutdown -- при завершении работы бота."
        )
        await safe_edit(event, bot, text, category_framework_kb())

    @dp.callback_query(CallbackDataFilter("fw:session"))
    async def show_session(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Session timeout\n\n"
            "SessionTimeoutMiddleware автоматически очищает FSM-состояние "
            "пользователя после заданного таймаута неактивности.\n\n"
            "session_mw = SessionTimeoutMiddleware(\n"
            "    storage,\n"
            "    timeout=600,  # 10 минут\n"
            "    on_timeout=on_session_timeout,\n"
            ")\n"
            "dp.add_middleware(session_mw)\n\n"
            "on_timeout -- опциональный callback, вызывается при истечении сессии.\n"
            "В этом боте таймаут: 10 минут."
        )
        await safe_edit(event, bot, text, category_framework_kb())
