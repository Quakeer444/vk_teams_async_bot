from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
    InlineKeyboardMarkup,
    KeyboardButton,
    StyleKeyboard,
)

from ..keyboards import back_to_main_kb, buttons_showcase_kb
from .utils import safe_edit


def register_buttons_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:btn"))
    async def show_buttons(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Кнопки и стили\n\n"
            "Здесь показаны три стиля кнопок, кнопка со ссылкой и несколько "
            "вариантов расположения кнопок в сообщении."
        )
        await safe_edit(event, bot, text, buttons_showcase_kb())

    @dp.callback_query(CallbackDataFilter("btn:alert"))
    async def handle_alert(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(
            query_id=event.query_id,
            text="Это popup (show_alert=True)",
            show_alert=True,
        )

    @dp.callback_query(CallbackDataFilter("btn:url"))
    async def handle_url(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(
            query_id=event.query_id,
            url="https://teams.vk.com/botapi/",
        )

    @dp.callback_query(CallbackDataFilter("btn:compose"))
    async def handle_compose(event: CallbackQueryEvent, bot: Bot):
        left = InlineKeyboardMarkup(buttons_in_row=1)
        left.add(
            KeyboardButton(
                text="Клавиатура A -- кнопка 1",
                callback_data="btn:comp:a1",
                style=StyleKeyboard.PRIMARY,
            ),
            KeyboardButton(
                text="Клавиатура A -- кнопка 2",
                callback_data="btn:comp:a2",
                style=StyleKeyboard.PRIMARY,
            ),
        )
        right = InlineKeyboardMarkup(buttons_in_row=1)
        right.add(
            KeyboardButton(
                text="Клавиатура B -- кнопка 1",
                callback_data="btn:comp:b1",
                style=StyleKeyboard.ATTENTION,
            ),
            KeyboardButton(
                text="Клавиатура B -- кнопка 2",
                callback_data="btn:comp:b2",
                style=StyleKeyboard.ATTENTION,
            ),
        )
        combined = left + right
        combined = combined + KeyboardButton(
            text="<< В главное меню", callback_data="menu:main"
        )
        await safe_edit(
            event,
            bot,
            "Композиция клавиатур (оператор +)\n\n"
            "Две клавиатуры объединены в одну через InlineKeyboardMarkup.__add__.\n"
            "Также можно добавить одну кнопку: keyboard + KeyboardButton(...).",
            combined,
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^btn:"))
    async def handle_button_click(event: CallbackQueryEvent, bot: Bot):
        style_name = event.callback_data.split(":", 1)[1]
        await bot.answer_callback_query(
            query_id=event.query_id,
            text=f"Вы нажали: {style_name}",
        )
