from vk_teams_async_bot import InlineKeyboardMarkup, KeyboardButton, StyleKeyboard

# -- Main Menu --

MAIN_MENU_TEXT = (
    "Демо-бот vk_teams_async_bot\n\n"
    "Здесь собраны примеры всех возможностей библиотеки.\n"
    "Выберите категорию:"
)


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    categories = [
        ("Быстрый старт", "menu:cat:start"),
        ("Сценарии ввода", "menu:cat:wiz"),
        ("Сообщения и файлы", "menu:cat:msg"),
        ("Фильтры", "menu:cat:flt"),
        ("Фреймворк", "menu:cat:fw"),
        ("Групповой чат", "menu:cat:grp"),
    ]
    for text, cb in categories:
        kb.add(KeyboardButton(text=text, callback_data=cb, style=StyleKeyboard.PRIMARY))
    return kb


def category_start_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Кнопки и стили", callback_data="menu:btn", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="Оформление текста",
            callback_data="menu:fmt",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Многоуровневое меню",
            callback_data="menu:nav",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def category_wiz_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Заказ пиццы по кнопкам",
            callback_data="menu:wzb",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Регистрация через сообщения",
            callback_data="menu:wzt",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Регистрация на событие",
            callback_data="menu:wzm",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Настройки с переключателями",
            callback_data="menu:tgl",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Мультивыбор с пагинацией",
            callback_data="menu:msel",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def category_msg_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Действия с сообщениями",
            callback_data="menu:msg",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Отправка и получение файлов",
            callback_data="menu:file",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def category_framework_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Зависимости в обработчиках",
            callback_data="menu:di",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Обработка ошибок",
            callback_data="menu:err",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Информация о боте",
            callback_data="fw:botinfo",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Middleware",
            callback_data="fw:middleware",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Lifecycle (startup/shutdown)",
            callback_data="fw:lifecycle",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Session timeout",
            callback_data="fw:session",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def category_group_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Действия в чате",
            callback_data="menu:chat",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="События чата", callback_data="menu:evt", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="Администрирование чата",
            callback_data="menu:adm",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def back_to_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Buttons Section --


def buttons_showcase_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    kb.add(
        KeyboardButton(text="BASE", callback_data="btn:base", style=StyleKeyboard.BASE),
        KeyboardButton(
            text="PRIMARY", callback_data="btn:primary", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="ATTENTION",
            callback_data="btn:attention",
            style=StyleKeyboard.ATTENTION,
        ),
    )
    kb.row(
        KeyboardButton(
            text="Документация VK Teams Bot API", url="https://teams.vk.com/botapi/"
        ),
    )
    kb.row(
        KeyboardButton(
            text="Одна в ряду", callback_data="btn:single", style=StyleKeyboard.PRIMARY
        ),
    )
    kb.add(
        KeyboardButton(text="Кнопка A", callback_data="btn:2a"),
        KeyboardButton(text="Кнопка B", callback_data="btn:2b"),
    )
    kb.row(
        KeyboardButton(
            text="Всплывающее уведомление",
            callback_data="btn:alert",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(
        KeyboardButton(
            text="Открыть URL по callback",
            callback_data="btn:url",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(
        KeyboardButton(
            text="Композиция клавиатур (+)",
            callback_data="btn:compose",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Navigation --

NAV_TREE = {
    "Начало работы": {
        "Установка": {
            "pip": "pip install vk-teams-async-bot",
            "poetry": "poetry add vk-teams-async-bot",
        },
        "Настройка": {
            "Токен": "Получите токен у @metabot",
            "URL API": "По умолчанию: https://api.internal.myteam.mail.ru",
        },
    },
    "Обработчики": {
        "Сообщения": {
            "@dp.message()": "Обрабатывает входящие сообщения",
            "@dp.command()": "Сокращение для CommandFilter",
        },
        "Callbacks": {
            "CallbackDataFilter": "Точное совпадение callback_data",
            "CallbackDataRegexpFilter": "Совпадение по регулярному выражению",
        },
    },
    "FSM": {
        "Состояния": {
            "StatesGroup": "Группирует связанные состояния",
            "State": "Одно состояние в группе",
        },
        "Хранилище": {
            "MemoryStorage": "Для разработки и тестов",
            "BaseStorage": "Базовый класс для Redis/DB",
        },
    },
}


def nav_level1_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for section in NAV_TREE:
        kb.add(
            KeyboardButton(
                text=section,
                callback_data=f"nav:l1:{section}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def nav_level2_kb(section: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    for item in NAV_TREE[section]:
        kb.add(
            KeyboardButton(
                text=item,
                callback_data=f"nav:l2:{section}:{item}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(KeyboardButton(text="<< Назад", callback_data="nav:back:l1"))
    return kb


def nav_level3_kb(section: str, item: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    for detail in NAV_TREE[section][item]:
        kb.add(
            KeyboardButton(
                text=detail,
                callback_data=f"nav:l3:{section}:{item}:{detail}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(KeyboardButton(text="<< Назад", callback_data=f"nav:back:l2:{section}"))
    return kb


def nav_level4_kb(section: str, item: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="<< Назад",
            callback_data=f"nav:back:l3:{section}:{item}",
        )
    )
    return kb


# -- Formatting --


def formatting_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Format API", callback_data="fmt:api", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="HTML-разметка", callback_data="fmt:html", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="MarkdownV2-разметка",
            callback_data="fmt:md",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Списки (Format API)",
            callback_data="fmt:lists",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Wizard (Buttons) --

PIZZA_SIZES = ["Маленькая", "Средняя", "Большая"]
PIZZA_CRUSTS = ["Тонкое", "Классическое", "С начинкой"]
PIZZA_SAUCES = ["Томатный", "BBQ", "Песто"]


def wzb_size_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for s in PIZZA_SIZES:
        kb.add(
            KeyboardButton(
                text=s,
                callback_data=f"wzb:size:{s.lower()}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzb:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


def wzb_crust_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for c in PIZZA_CRUSTS:
        kb.add(
            KeyboardButton(
                text=c,
                callback_data=f"wzb:crust:{c.lower()}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(
        KeyboardButton(text="<< Назад", callback_data="wzb:back:size"),
        KeyboardButton(
            text="Отмена", callback_data="wzb:cancel", style=StyleKeyboard.ATTENTION
        ),
    )
    return kb


def wzb_sauce_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for s in PIZZA_SAUCES:
        kb.add(
            KeyboardButton(
                text=s,
                callback_data=f"wzb:sauce:{s.lower()}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(
        KeyboardButton(text="<< Назад", callback_data="wzb:back:crust"),
        KeyboardButton(
            text="Отмена", callback_data="wzb:cancel", style=StyleKeyboard.ATTENTION
        ),
    )
    return kb


def wzb_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Подтвердить", callback_data="wzb:confirm", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(text="<< Назад", callback_data="wzb:back:sauce"),
    )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzb:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


# -- Wizard (Text) --


def wzt_back_cancel_kb(back_step: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    if back_step:
        kb.add(KeyboardButton(text="<< Назад", callback_data=f"wzt:back:{back_step}"))
    kb.add(
        KeyboardButton(
            text="Отмена", callback_data="wzt:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


def wzt_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Подтвердить", callback_data="wzt:confirm", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(text="<< Назад", callback_data="wzt:back:phone"),
    )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzt:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


# -- Wizard (Mixed) --

EVENT_TYPES = ["Конференция", "Митап", "Воркшоп"]
MEAL_PREFS = ["Стандартное", "Вегетарианское", "Веганское"]


def wzm_event_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for e in EVENT_TYPES:
        kb.add(
            KeyboardButton(
                text=e,
                callback_data=f"wzm:event:{e.lower()}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzm:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


def wzm_attendees_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(text="<< Назад", callback_data="wzm:back:event"),
        KeyboardButton(
            text="Отмена", callback_data="wzm:cancel", style=StyleKeyboard.ATTENTION
        ),
    )
    return kb


def wzm_meal_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    for m in MEAL_PREFS:
        kb.add(
            KeyboardButton(
                text=m,
                callback_data=f"wzm:meal:{m.lower()}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(
        KeyboardButton(text="<< Назад", callback_data="wzm:back:attendees"),
        KeyboardButton(
            text="Отмена", callback_data="wzm:cancel", style=StyleKeyboard.ATTENTION
        ),
    )
    return kb


def wzm_notes_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Пропустить", callback_data="wzm:skip", style=StyleKeyboard.BASE
        ),
        KeyboardButton(text="<< Назад", callback_data="wzm:back:meal"),
    )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzm:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


def wzm_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Подтвердить", callback_data="wzm:confirm", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(text="<< Назад", callback_data="wzm:back:notes"),
    )
    kb.row(
        KeyboardButton(
            text="Отмена", callback_data="wzm:cancel", style=StyleKeyboard.ATTENTION
        )
    )
    return kb


# -- Toggle Settings --

DEFAULT_SETTINGS = {
    "notifications": True,
    "dark_mode": False,
    "auto_reply": False,
    "sound": True,
    "read_receipts": True,
}

SETTING_LABELS = {
    "notifications": "Уведомления",
    "dark_mode": "Темная тема",
    "auto_reply": "Автоответ",
    "sound": "Звук",
    "read_receipts": "Отчеты о прочтении",
}


def toggle_settings_kb(settings: dict[str, bool]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    for key, label in SETTING_LABELS.items():
        is_on = settings.get(key, False)
        text = f"[ВКЛ] {label}" if is_on else f"[ВЫКЛ] {label}"
        style = StyleKeyboard.PRIMARY if is_on else StyleKeyboard.BASE
        kb.add(KeyboardButton(text=text, callback_data=f"tgl:{key}", style=style))
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Multi-Select --

LANGUAGES = [
    "Python",
    "Rust",
    "Go",
    "TypeScript",
    "Java",
    "C++",
    "Kotlin",
    "Swift",
    "Ruby",
    "PHP",
    "Scala",
    "Haskell",
    "Elixir",
    "Dart",
    "Lua",
    "Zig",
    "OCaml",
    "Julia",
]
MSEL_PAGE_SIZE = 6


def multiselect_kb(selected: set[str], page: int = 0) -> InlineKeyboardMarkup:
    total_pages = (len(LANGUAGES) + MSEL_PAGE_SIZE - 1) // MSEL_PAGE_SIZE
    page = max(0, min(page, total_pages - 1))
    start = page * MSEL_PAGE_SIZE
    page_items = LANGUAGES[start : start + MSEL_PAGE_SIZE]

    kb = InlineKeyboardMarkup(buttons_in_row=2)
    lang_buttons = []
    for lang in page_items:
        is_sel = lang in selected
        text = f"[v] {lang}" if is_sel else f"[ ] {lang}"
        style = StyleKeyboard.PRIMARY if is_sel else StyleKeyboard.BASE
        lang_buttons.append(
            KeyboardButton(text=text, callback_data=f"msel:toggle:{lang}", style=style)
        )
    kb.add(*lang_buttons)

    nav_buttons: list[KeyboardButton] = []
    if page > 0:
        nav_buttons.append(
            KeyboardButton(
                text="<< Назад",
                callback_data=f"msel:page:{page - 1}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    nav_buttons.append(
        KeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}",
            callback_data="msel:noop",
            style=StyleKeyboard.PRIMARY,
        )
    )
    if page < total_pages - 1:
        nav_buttons.append(
            KeyboardButton(
                text="Вперед >>",
                callback_data=f"msel:page:{page + 1}",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(*nav_buttons)

    kb.row(
        KeyboardButton(
            text="Очистить все",
            callback_data="msel:clear",
            style=StyleKeyboard.ATTENTION,
        )
    )
    if selected:
        kb.row(
            KeyboardButton(
                text=f"Далее >> (выбрано: {len(selected)})",
                callback_data="msel:next",
                style=StyleKeyboard.PRIMARY,
            )
        )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def multiselect_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Подтвердить",
            callback_data="msel:confirm",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(text="<< Назад", callback_data="msel:back"),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Files --


def files_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Отправить тестовое изображение",
            callback_data="file:send:img",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Отправить тестовое голосовое",
            callback_data="file:send:voice",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Получить файл",
            callback_data="file:receive",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Events --


def events_info_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Остановить отслеживание",
            callback_data="evt:stop",
            style=StyleKeyboard.ATTENTION,
        )
    )
    kb.add(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Messages --


def messages_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Ответить", callback_data="msg:reply", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="Переслать", callback_data="msg:forward", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="Редактировать", callback_data="msg:edit", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="Удалить", callback_data="msg:delete", style=StyleKeyboard.PRIMARY
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- Filters --


def filters_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="По вложениям", callback_data="flt:parts", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="По тексту / пользователю",
            callback_data="flt:text",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Составные фильтры",
            callback_data="flt:composite",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Продвинутые фильтры",
            callback_data="flt:advanced",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


def filter_parts_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="FileFilter",
            callback_data="flt:part:file",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="VoiceFilter",
            callback_data="flt:part:voice",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="StickerFilter",
            callback_data="flt:part:sticker",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="MentionFilter",
            callback_data="flt:part:mention",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="ReplyFilter",
            callback_data="flt:part:reply",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="ForwardFilter",
            callback_data="flt:part:forward",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< Назад", callback_data="menu:flt"))
    return kb


def filter_text_user_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="RegexpFilter (email)",
            callback_data="flt:txt:regexp",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="TagFilter (hello/hi/hey)",
            callback_data="flt:txt:tag",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="CommandFilter (/demo)",
            callback_data="flt:txt:cmd",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="TextFilter",
            callback_data="flt:text_filter",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="FromUserFilter",
            callback_data="flt:fromuser",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< Назад", callback_data="menu:flt"))
    return kb


# Keep alias for backward compat within this file
filter_text_kb = filter_text_user_kb


def filter_composite_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="AND: ReplyFilter & FileFilter",
            callback_data="flt:comp:and",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="OR: FileFilter | VoiceFilter",
            callback_data="flt:comp:or",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="NOT: ~StickerFilter",
            callback_data="flt:comp:not",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< Назад", callback_data="menu:flt"))
    return kb


def filter_advanced_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="RegexpTextPartsFilter",
            callback_data="flt:adv:regexp",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="MessageTextPartFromNickFilter",
            callback_data="flt:adv:nick",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="CallbackDataRegexpFilter (info)",
            callback_data="flt:adv:cbregexp",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="ChatTypeFilter",
            callback_data="flt:chattype",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="ChatIdFilter", callback_data="flt:chatid", style=StyleKeyboard.PRIMARY
        ),
        KeyboardButton(
            text="FileTypeFilter",
            callback_data="flt:filetype",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="MentionUserFilter",
            callback_data="flt:mention_user",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< Назад", callback_data="menu:flt"))
    return kb


# -- Chat Ops --


def chat_ops_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Информация о чате",
            callback_data="chat:info",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text='Действие "печатает"',
            callback_data="chat:typing",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text='Действие "смотрит"',
            callback_data="chat:looking",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Закрепить сообщение",
            callback_data="chat:pin",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb


# -- DI --


def di_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=1)
    kb.add(
        KeyboardButton(
            text="Синхронная зависимость",
            callback_data="di:sync",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Асинхронная зависимость",
            callback_data="di:async",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Генератор-зависимость",
            callback_data="di:generator",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Annotated-зависимость",
            callback_data="di:annotated",
            style=StyleKeyboard.PRIMARY,
        ),
    )
    kb.row(KeyboardButton(text="<< В главное меню", callback_data="menu:main"))
    return kb
