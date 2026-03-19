from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
)

from ..keyboards import (
    NAV_TREE,
    nav_level1_kb,
    nav_level2_kb,
    nav_level3_kb,
    nav_level4_kb,
)
from .utils import safe_edit

NAV_INTRO = "Многоуровневое меню\n\nСправочник по библиотеке vk_teams_async_bot.\nВыберите раздел:"


def register_navigation_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:nav"))
    async def show_nav(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(event, bot, NAV_INTRO, nav_level1_kb())

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l1:"))
    async def nav_l1(event: CallbackQueryEvent, bot: Bot):
        section = event.callback_data.split(":", 2)[2]
        await safe_edit(
            event,
            bot,
            f"{section}\n\nВыберите тему:",
            nav_level2_kb(section),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l2:"))
    async def nav_l2(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item = parts[2], parts[3]
        await safe_edit(
            event,
            bot,
            f"{section} > {item}\n\nВыберите пункт:",
            nav_level3_kb(section, item),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l3:"))
    async def nav_l3(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item, detail = parts[2], parts[3], parts[4]
        leaf = NAV_TREE[section][item][detail]
        await safe_edit(
            event,
            bot,
            f"{section} > {item} > {detail}\n\n{leaf}",
            nav_level4_kb(section, item),
        )

    @dp.callback_query(CallbackDataFilter("nav:back:l1"))
    async def nav_back_l1(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(event, bot, NAV_INTRO, nav_level1_kb())

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:back:l2:"))
    async def nav_back_l2(event: CallbackQueryEvent, bot: Bot):
        section = event.callback_data.split(":")[3]
        await safe_edit(
            event,
            bot,
            f"{section}\n\nВыберите тему:",
            nav_level2_kb(section),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:back:l3:"))
    async def nav_back_l3(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item = parts[3], parts[4]
        await safe_edit(
            event,
            bot,
            f"{section} > {item}\n\nВыберите пункт:",
            nav_level3_kb(section, item),
        )
