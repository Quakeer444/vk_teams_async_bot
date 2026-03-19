from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    Dispatcher,
    Format,
    ParseMode,
    StyleType,
)

from ..keyboards import back_to_main_kb, formatting_menu_kb
from .utils import safe_edit


def register_formatting_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:fmt"))
    async def show_formatting(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Оформление текста\n\nСравните три способа форматирования сообщений.\nВыберите режим:",
            formatting_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("fmt:api"))
    async def fmt_api(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Жирный текст. "
            "Курсивный текст. "
            "Подчеркнутый. "
            "Зачеркнутый. "
            "Инлайн код. "
            "Пример ссылки. "
            "Форматированный блок. "
            "Цитата."
        )
        fmt = Format()
        offset = 0
        # Bold: "Жирный текст." = 13
        fmt.add(StyleType.BOLD, offset, 13)
        offset += 14
        # Italic: "Курсивный текст." = 16
        fmt.add(StyleType.ITALIC, offset, 16)
        offset += 17
        # Underline: "Подчеркнутый." = 13
        fmt.add(StyleType.UNDERLINE, offset, 13)
        offset += 14
        # Strikethrough: "Зачеркнутый." = 12
        fmt.add(StyleType.STRIKETHROUGH, offset, 12)
        offset += 13
        # Inline code: "Инлайн код." = 11
        fmt.add(StyleType.INLINE_CODE, offset, 11)
        offset += 12
        # Link: "Пример ссылки." = 14
        fmt.add(StyleType.LINK, offset, 14, url="https://teams.vk.com/botapi/")
        offset += 15
        # Pre: "Форматированный блок." = 21
        fmt.add(StyleType.PRE, offset, 21)
        offset += 22
        # Quote: "Цитата." = 7
        fmt.add(StyleType.QUOTE, offset, 7)

        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            format_=fmt,
            inline_keyboard_markup=back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("fmt:html"))
    async def fmt_html(event: CallbackQueryEvent, bot: Bot):
        text = (
            "<b>Жирный</b> | <i>Курсив</i> | <u>Подчеркнутый</u> | <s>Зачеркнутый</s>\n"
            '<a href="https://teams.vk.com/botapi/">Ссылка</a>\n'
            "<code>инлайн код</code>\n"
            "<pre>форматированный блок</pre>\n"
            "Список:\n- элемент 1\n- элемент 2\n- элемент 3"
        )
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            inline_keyboard_markup=back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("fmt:md"))
    async def fmt_md(event: CallbackQueryEvent, bot: Bot):
        text = (
            "*Жирный* | _Курсив_ | ~Зачеркнутый~\n"
            "`инлайн код`\n"
            "```\nформатированный блок\n```\n"
            "[Ссылка](https://teams.vk.com/botapi/)"
        )
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWNV2,
            inline_keyboard_markup=back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("fmt:lists"))
    async def fmt_lists(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Нумерованный список:\n"
            "Первый элемент\n"
            "Второй элемент\n"
            "Третий элемент\n"
            "Маркированный список:\n"
            "Яблоко\n"
            "Банан\n"
            "Вишня"
        )
        fmt = Format()
        # "Нумерованный список:\n" = 21 chars
        offset = 21
        # Each item: "Первый элемент\n" = 15, "Второй элемент\n" = 15, "Третий элемент\n" = 15
        fmt.add(StyleType.ORDERED_LIST, offset, 14)
        offset += 15
        fmt.add(StyleType.ORDERED_LIST, offset, 14)
        offset += 15
        fmt.add(StyleType.ORDERED_LIST, offset, 14)
        offset += 15
        # "Маркированный список:\n" = 22 chars
        offset += 22
        # "Яблоко\n" = 7, "Банан\n" = 6, "Вишня" = 5
        fmt.add(StyleType.UNORDERED_LIST, offset, 6)
        offset += 7
        fmt.add(StyleType.UNORDERED_LIST, offset, 5)
        offset += 6
        fmt.add(StyleType.UNORDERED_LIST, offset, 5)

        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            format_=fmt,
            inline_keyboard_markup=back_to_main_kb(),
        )
