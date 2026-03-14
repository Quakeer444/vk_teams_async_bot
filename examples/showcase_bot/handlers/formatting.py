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


async def safe_edit(event: CallbackQueryEvent, bot: Bot, text: str, keyboard=None, **kwargs):
    await bot.answer_callback_query(query_id=event.query_id)
    if event.message:
        await bot.edit_text(
            chat_id=event.chat.chat_id,
            msg_id=event.message.msg_id,
            text=text,
            inline_keyboard_markup=keyboard,
            **kwargs,
        )
    else:
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=keyboard,
            **kwargs,
        )


def register_formatting_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:fmt"))
    async def show_formatting(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Демо форматирования\n\nВыберите режим форматирования:",
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
