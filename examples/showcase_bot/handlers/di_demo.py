from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, AsyncGenerator

import aiohttp

from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    Dispatcher,
)

from ..keyboards import di_menu_kb


@dataclass
class AppConfig:
    app_name: str
    version: str


def get_config() -> AppConfig:
    return AppConfig(app_name="Showcase Bot", version="1.0.0")


async def get_timestamp() -> datetime:
    return datetime.now()


async def get_http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


def register_di_dependencies(bot: Bot) -> None:
    bot.depends.append(get_config)
    bot.depends.append(get_timestamp)
    bot.depends.append(get_http_session)


def register_di_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:di"))
    async def show_di(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        text = (
            "Dependency Injection (DI)\n\n"
            "Бот автоматически подставляет нужные объекты в обработчик "
            "по аннотации типа параметра. Достаточно указать тип -- "
            "фреймворк сам найдет и вызовет нужную функцию.\n\n"
            "3 вида зависимостей:\n"
            "-- Синхронная (def -> T) -- для легких вещей без I/O: конфиги, настройки\n"
            "-- Асинхронная (async def -> T) -- когда нужен await: БД, кэш, внешние API\n"
            "-- Генератор (async yield T) -- ресурс с очисткой: "
            "сессии, подключения, блокировки (teardown гарантирован)\n\n"
            "Выберите пример:"
        )
        if event.message:
            await bot.edit_text(
                chat_id=event.chat.chat_id,
                msg_id=event.message.msg_id,
                text=text,
                inline_keyboard_markup=di_menu_kb(),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=text,
                inline_keyboard_markup=di_menu_kb(),
            )

    @dp.callback_query(CallbackDataFilter("di:sync"))
    async def di_sync(event: CallbackQueryEvent, bot: Bot, config: AppConfig):
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f"Синхронная зависимость (def -> T)\n\n"
                f"get_config() вызвана автоматически, "
                f"результат передан в параметр config: AppConfig.\n\n"
                f"Приложение: {config.app_name}\n"
                f"Версия: {config.version}"
            ),
            inline_keyboard_markup=di_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("di:async"))
    async def di_async(event: CallbackQueryEvent, bot: Bot, timestamp: datetime):
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f"Асинхронная зависимость (async def -> T)\n\n"
                f"await get_timestamp() вызвана автоматически, "
                f"результат передан в параметр timestamp: datetime.\n\n"
                f"Время сервера: {timestamp.isoformat()}"
            ),
            inline_keyboard_markup=di_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("di:generator"))
    async def di_gen(event: CallbackQueryEvent, bot: Bot, session: aiohttp.ClientSession):
        await bot.answer_callback_query(query_id=event.query_id)
        try:
            async with session.get("https://httpbin.org/ip") as resp:
                data = await resp.json()
            ip_info = data.get("origin", "unknown")
        except Exception as e:
            ip_info = f"Ошибка: {e}"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f"Генератор-зависимость (async yield T)\n\n"
                f"HTTP-сессия создана до обработчика и закрыта после. "
                f"Очистка гарантирована даже при ошибке.\n\n"
                f"IP бота: {ip_info}"
            ),
            inline_keyboard_markup=di_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("di:annotated"))
    async def di_annotated(event: CallbackQueryEvent, bot: Bot, cfg: Annotated[AppConfig, get_config]):
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f"Annotated-зависимость\n\n"
                f"Параметр объявлен как Annotated[AppConfig, get_config] -- "
                f"вторым аргументом указана конкретная функция-провайдер.\n"
                f"Это позволяет иметь несколько провайдеров одного типа.\n\n"
                f"Приложение: {cfg.app_name}\n"
                f"Версия: {cfg.version}"
            ),
            inline_keyboard_markup=di_menu_kb(),
        )
