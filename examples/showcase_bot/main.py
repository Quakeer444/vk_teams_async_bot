import asyncio
import logging
import os
import time

from vk_teams_async_bot import (
    BaseMiddleware,
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    CommandFilter,
    Dispatcher,
    FSMContext,
    MemoryStorage,
    NewMessageEvent,
    SessionTimeoutMiddleware,
)

from .handlers import register_all_handlers
from .handlers.di_demo import register_di_dependencies
from .keyboards import main_menu_kb

import argparse

_parser = argparse.ArgumentParser()
_parser.add_argument("--log-level", default="INFO")
_args, _ = _parser.parse_known_args()
logging.basicConfig(
    level=getattr(logging, _args.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("showcase_bot")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        chat_obj = getattr(event, "chat", None)
        msg_obj = getattr(event, "message", None)
        chat_id = (
            getattr(chat_obj, "chat_id", None)
            or getattr(getattr(msg_obj, "chat", None), "chat_id", None)
            or "?"
        )
        user_id = getattr(getattr(event, "from_", None), "user_id", None) or "?"
        event_type = getattr(event, "type", "?")
        start = time.monotonic()
        try:
            result = await handler(event, data)
            elapsed = (time.monotonic() - start) * 1000
            logger.info("Event %s chat=%s user=%s processed in %.1fms", event_type, chat_id, user_id, elapsed)
            return result
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            logger.exception("Event %s chat=%s user=%s failed after %.1fms", event_type, chat_id, user_id, elapsed)
            raise


async def on_session_timeout(chat_id: str, user_id: str) -> None:
    logger.info("Session expired for chat=%s user=%s", chat_id, user_id)


async def main() -> None:
    bot_token = os.environ.get("BOT_TOKEN", "")
    api_url = os.environ.get("API_URL", "https://api.internal.myteam.mail.ru")

    if not bot_token:
        logger.error("BOT_TOKEN environment variable is required")
        return

    # MemoryStorage -- demo only, use BaseStorage subclass with Redis/DB in production
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    session_mw = SessionTimeoutMiddleware(
        storage,
        timeout=600,
        on_timeout=on_session_timeout,
    )
    dp.add_middleware(session_mw)
    dp.add_middleware(LoggingMiddleware())

    async with Bot(bot_token, url=api_url) as bot:
        # Register DI dependencies
        register_di_dependencies(bot)

        # /start command
        @dp.message(CommandFilter("start"))
        async def cmd_start(event: NewMessageEvent, bot: Bot):
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=(
                    "Демо-бот vk_teams_async_bot\n\n"
                    "Здесь собраны примеры кнопок, меню, оформления текста, пошаговых "
                    "сценариев, файлов, событий и фильтров.\n"
                    "Выберите пример и сразу попробуйте его в чате."
                ),
                inline_keyboard_markup=main_menu_kb(),
            )

        # /cancel command -- exit any wizard/state
        @dp.message(CommandFilter("cancel"))
        async def cmd_cancel(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
            state = await fsm_context.get_state()
            if state is not None:
                await fsm_context.clear()
                await bot.send_text(
                    chat_id=event.chat.chat_id,
                    text="Отменено. Главное меню:",
                    inline_keyboard_markup=main_menu_kb(),
                )
            else:
                await bot.send_text(
                    chat_id=event.chat.chat_id,
                    text="Нечего отменять.",
                )

        # /help command -- using @dp.command() shortcut (equivalent to CommandFilter)
        @dp.command("help")
        async def cmd_help(event: NewMessageEvent, bot: Bot):
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=(
                    "Доступные команды:\n"
                    "/start -- главное меню\n"
                    "/help -- это сообщение\n"
                    "/cancel -- выход из любого пошагового сценария\n"
                    "/demo -- демо команда фильтров\n"
                    "/demo_cmd -- демо @dp.command()\n\n"
                    "Используйте кнопки меню для изучения всех возможностей."
                ),
            )

        @dp.command("demo_cmd")
        async def cmd_demo_cmd(event: NewMessageEvent, bot: Bot):
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=(
                    "Это обработчик зарегистрирован через @dp.command(\"demo_cmd\").\n\n"
                    "@dp.command(cmd) -- это сокращение для @dp.message(CommandFilter(cmd)).\n"
                    "Оба варианта полностью эквивалентны."
                ),
            )

        # Back to main menu callback
        @dp.callback_query(CallbackDataFilter("menu:main"))
        async def back_to_main(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
            await fsm_context.clear()
            await bot.answer_callback_query(query_id=event.query_id)
            if event.message:
                await bot.edit_text(
                    chat_id=event.chat.chat_id,
                    msg_id=event.message.msg_id,
                    text=(
                        "Демо-бот vk_teams_async_bot\n\n"
                        "Здесь собраны примеры кнопок, меню, оформления текста, пошаговых "
                        "сценариев, файлов, событий и фильтров.\n"
                        "Выберите пример и сразу попробуйте его в чате."
                    ),
                    inline_keyboard_markup=main_menu_kb(),
                )
            else:
                await bot.send_text(
                    chat_id=event.chat.chat_id,
                    text=(
                        "Демо-бот vk_teams_async_bot\n\n"
                        "Здесь собраны примеры кнопок, меню, оформления текста, пошаговых "
                        "сценариев, файлов, событий и фильтров.\n"
                        "Выберите пример и сразу попробуйте его в чате."
                    ),
                    inline_keyboard_markup=main_menu_kb(),
                )

        # Register all section handlers
        register_all_handlers(dp, storage)

        # Lifecycle hooks
        @bot.on_startup
        async def startup(bot: Bot):
            info = await bot.get_self()
            logger.info("Bot started: %s (@%s)", info.first_name, info.nick)

        @bot.on_shutdown
        async def shutdown(bot: Bot):
            await session_mw.close()
            logger.info("Bot stopped")

        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
