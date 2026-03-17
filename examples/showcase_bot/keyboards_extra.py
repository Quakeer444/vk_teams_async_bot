import os

from vk_teams_async_bot import InlineKeyboardMarkup, KeyboardButton, StyleKeyboard


# -- Error Demo --

def error_demo_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(text="APIError -- редактирование несуществующего", callback_data="err:api", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Иерархия ошибок", callback_data="err:hierarchy", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Безопасный try/except", callback_data="err:safe", style=StyleKeyboard.PRIMARY),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Chat Admin --

def chat_admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(text="Администраторы чата", callback_data="adm:admins", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Участники чата (пагинация)", callback_data="adm:members", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Заблокированные пользователи", callback_data="adm:blocked", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Ожидающие подтверждения", callback_data="adm:pending", style=StyleKeyboard.PRIMARY),
    )
    admin_mode = os.environ.get("SHOWCASE_ADMIN_MODE") == "1"
    style = StyleKeyboard.ATTENTION if admin_mode else StyleKeyboard.BASE
    kb.add(
        KeyboardButton(text="Изменить название чата", callback_data="adm:title", style=style),
        KeyboardButton(text="Изменить описание чата", callback_data="adm:about", style=style),
        KeyboardButton(text="Изменить правила чата", callback_data="adm:rules", style=style),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def admin_confirm_kb(action: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(text="Подтвердить", callback_data=f"adm:confirm:{action}", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Отмена", callback_data="menu:adm", style=StyleKeyboard.ATTENTION),
    )
    return kb
