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


def register_navigation_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:nav"))
    async def show_nav(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(event, bot, "Демо навигации -- Уровень 1\n\nВыберите раздел:", nav_level1_kb())

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l1:"))
    async def nav_l1(event: CallbackQueryEvent, bot: Bot):
        section = event.callback_data.split(":")[2]
        await safe_edit(
            event, bot,
            f"Уровень 2 -- Раздел {section}\n\nВыберите элемент:",
            nav_level2_kb(section),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l2:"))
    async def nav_l2(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item = parts[2], parts[3]
        await safe_edit(
            event, bot,
            f"Уровень 3 -- {section} > {item}\n\nВыберите деталь:",
            nav_level3_kb(section, item),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:l3:"))
    async def nav_l3(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item, detail = parts[2], parts[3], parts[4]
        leaf = NAV_TREE[section][item][detail]
        await safe_edit(
            event, bot,
            f"Уровень 4 -- {section} > {item} > {detail}\n\n{leaf}",
            nav_level4_kb(section, item),
        )

    @dp.callback_query(CallbackDataFilter("nav:back:l1"))
    async def nav_back_l1(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(event, bot, "Демо навигации -- Уровень 1\n\nВыберите раздел:", nav_level1_kb())

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:back:l2:"))
    async def nav_back_l2(event: CallbackQueryEvent, bot: Bot):
        section = event.callback_data.split(":")[3]
        await safe_edit(
            event, bot,
            f"Уровень 2 -- Раздел {section}\n\nВыберите элемент:",
            nav_level2_kb(section),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^nav:back:l3:"))
    async def nav_back_l3(event: CallbackQueryEvent, bot: Bot):
        parts = event.callback_data.split(":")
        section, item = parts[3], parts[4]
        await safe_edit(
            event, bot,
            f"Уровень 3 -- {section} > {item}\n\nВыберите деталь:",
            nav_level3_kb(section, item),
        )
