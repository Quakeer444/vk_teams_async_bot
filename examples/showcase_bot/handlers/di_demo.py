from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator

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
            "Демо внедрения зависимостей\n\n"
            "DI разрешается автоматически по аннотациям типов в сигнатуре обработчика.\n"
            "Выберите тип зависимости для теста:"
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
            text=f"Результат синхронного DI:\n\nПриложение: {config.app_name}\nВерсия: {config.version}",
            inline_keyboard_markup=di_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("di:async"))
    async def di_async(event: CallbackQueryEvent, bot: Bot, timestamp: datetime):
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Результат асинхронного DI:\n\nВремя сервера: {timestamp.isoformat()}",
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
            text=f"Результат генератор-DI:\n\nIP бота: {ip_info}",
            inline_keyboard_markup=di_menu_kb(),
        )
