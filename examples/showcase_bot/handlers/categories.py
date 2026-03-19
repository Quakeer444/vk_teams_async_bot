from vk_teams_async_bot import Bot, CallbackDataFilter, CallbackQueryEvent, Dispatcher

from ..keyboards import (
    category_framework_kb,
    category_group_kb,
    category_msg_kb,
    category_start_kb,
    category_wiz_kb,
    filters_menu_kb,
)
from .utils import safe_edit


def register_category_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:cat:start"))
    async def cat_start(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Быстрый старт\n\nОсновы работы с ботом: кнопки, форматирование, навигация.",
            category_start_kb(),
        )

    @dp.callback_query(CallbackDataFilter("menu:cat:wiz"))
    async def cat_wiz(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Сценарии ввода\n\nПошаговые формы, переключатели, мультивыбор.",
            category_wiz_kb(),
        )

    @dp.callback_query(CallbackDataFilter("menu:cat:msg"))
    async def cat_msg(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Сообщения и файлы\n\nОтправка, редактирование, пересылка, файлы.",
            category_msg_kb(),
        )

    @dp.callback_query(CallbackDataFilter("menu:cat:flt"))
    async def cat_flt(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Фильтры сообщений\n\nВыберите, какие фильтры хотите посмотреть:",
            filters_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("menu:cat:fw"))
    async def cat_fw(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Фреймворк\n\nDI, ошибки, middleware, lifecycle.",
            category_framework_kb(),
        )

    @dp.callback_query(CallbackDataFilter("menu:cat:grp"))
    async def cat_grp(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Групповой чат\n\nДействия в чате, события, администрирование.",
            category_group_kb(),
        )
