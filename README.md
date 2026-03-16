[![PyPI Version](https://img.shields.io/pypi/v/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![Python](https://img.shields.io/pypi/pyversions/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://github.com/Quakeer444/vk_teams_async_bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Quakeer444/vk_teams_async_bot/actions)

# vk-teams-async-bot

`vk-teams-async-bot` -- асинхронная Python-библиотека для создания ботов VK Teams.

Она объединяет две роли в одном пакете:

- удобный клиент для VK Teams Bot API;
- фреймворк для long polling, обработчиков, фильтров, FSM, middleware и dependency injection.

## Почему библиотека удобна

- В репозитории есть полноценный `showcase bot` в `examples/showcase_bot`: он показывает сообщения, кнопки, навигацию и пагинацию, FSM-сценарии, форматирование, файлы, события, операции с сообщениями и dependency injection.
- Один пакет закрывает и прямую работу с VK Teams Bot API, и событийную обработку бота через polling, диспетчер, фильтры и состояния.
- Типизированные модели, фильтры, middleware и DI помогают писать обработчики понятнее и с меньшим количеством ручного кода.

## Context7

Этот раздел нужен только тем, кто работает через MCP/LLM-ассистентов. Если вы читаете README как обычный разработчик, его можно пропустить.

Если вы используете MCP `Context7`, документация по `vk-teams-async-bot` уже доступна в каталоге:

https://context7.com/quakeer444/vk_teams_async_bot

Чтобы ассистент автоматически обращался к ней, добавьте в `CLAUDE.md` или `AGENTS.md` такую инструкцию:

```md
Always use Context7 when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
For `vk-teams-async-bot` documentation use Context7: https://context7.com/quakeer444/vk_teams_async_bot
```

## Содержание

- [Почему библиотека удобна](#почему-библиотека-удобна)
- [Context7](#context7)
- [Что это за библиотека](#что-это-за-библиотека)
- [Что есть внутри](#что-есть-внутри)
- [Что важно знать заранее](#что-важно-знать-заранее)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Основные понятия](#основные-понятия)
- [Примеры](#примеры)
  - [Обработка команд](#обработка-команд)
  - [Инлайн-клавиатура](#инлайн-клавиатура)
  - [Фильтры и их композиция](#фильтры-и-их-композиция)
  - [Форматирование текста](#форматирование-текста)
  - [FSM: пошаговые сценарии](#fsm-пошаговые-сценарии)
  - [Middleware](#middleware)
  - [Работа с файлами](#работа-с-файлами)
  - [Dependency Injection](#dependency-injection)
  - [Хуки жизненного цикла](#хуки-жизненного-цикла)
- [Поддерживаемые события](#поддерживаемые-события)
- [Реализованные методы API](#реализованные-методы-api)
- [Обработка ошибок и retry](#обработка-ошибок-и-retry)
- [Примеры в репозитории](#примеры-в-репозитории)
- [Как устроен проект](#как-устроен-проект)
- [Локальная разработка](#локальная-разработка)
- [Миграция с 0.2.x](#миграция-с-02x)
- [Лицензия](#лицензия)

## Что это за библиотека

Эта библиотека подходит, если вы хотите:

- быстро поднять бота на Python без ручной работы с HTTP-запросами;
- обрабатывать события через декораторы `@dp.message()`, `@dp.callback_query()` и другие;
- использовать типизированные модели событий и ответов API;
- строить пошаговые сценарии через FSM;
- добавлять middleware и зависимости в обработчики;
- при необходимости вызывать методы API напрямую через `Bot`.

Она особенно удобна, когда нужен один пакет и для прямой работы с VK Teams Bot API, и для событийной обработки бота через декораторы, фильтры и состояния.

## Что есть внутри

- `Bot` -- основной объект. Управляет HTTP-сессией, long polling и lifecycle hooks.
- `Dispatcher` -- маршрутизирует события к подходящим обработчикам.
- Обработчики событий -- сообщения, callback-запросы, изменения сообщений, pin/unpin, вход и выход участников.
- Фильтры -- команды, regex, callback data, части сообщения, состояния и логические комбинации.
- FSM -- `StatesGroup`, `State`, `FSMContext`, `BaseStorage`, `MemoryStorage`.
- Middleware -- цепочка обработки до и после вызова обработчика.
- Dependency Injection -- зависимости по аннотациям типов и `Annotated`.
- Типизированные модели -- события, сообщения, файлы, клавиатуры, ответы API, перечисления.

## Что важно знать заранее

- Требуется `Python 3.11+`.
- Библиотека использует `long polling`. Webhook-режима сейчас нет.
- `CommandFilter("start")` совпадает с сообщением `/start`. Слэш в аргумент фильтра передавать не нужно.
- `Dispatcher` вызывает только первый обработчик, который подошел под событие и фильтры.
- События обрабатываются параллельно. Лимит задается через `Bot(..., max_concurrent_handlers=...)`, по умолчанию это `100`.
- Если у `Dispatcher` подключено FSM-хранилище, события одного и того же `(chat_id, user_id)` выполняются последовательно, чтобы не было гонок по состоянию.
- `MemoryStorage` удобно использовать в разработке. Для продакшена лучше реализовать `BaseStorage` поверх Redis или БД.
- Методы `create_chat()` и `add_chat_members()` доступны только в специальных on-premise сборках VK Teams и требуют настройки со стороны администратора.
- Неизвестные типы событий парсятся в `RawUnknownEvent` и пропускаются диспетчером без падения приложения.

## Установка

```bash
pip install vk-teams-async-bot
```

или:

```bash
poetry add vk-teams-async-bot
```

## Быстрый старт

1. Получите токен бота у [Metabot](https://teams.vk.com/profile/70001).
2. Установите переменную окружения `BOT_TOKEN`.
3. Если вы работаете с on-premise инсталляцией, при необходимости задайте `API_URL`.
4. Создайте файл `bot.py`:

```python
import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

bot = Bot(
    bot_token=os.environ["BOT_TOKEN"],
    url=os.getenv("API_URL", "https://api.internal.myteam.mail.ru"),
)
dp = Dispatcher()


@dp.message()
async def echo(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text=event.text or "")


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

Запуск:

```bash
# Пример для macOS / Linux
export BOT_TOKEN="your_token"
python bot.py
```

На Windows задайте `BOT_TOKEN` любым привычным способом, затем запустите `python bot.py`.

Что здесь происходит:

- `Bot` создает HTTP-клиент и знает, как обращаться к VK Teams Bot API;
- `Dispatcher` хранит обработчики событий;
- `@dp.message()` говорит: "вызывать эту функцию на каждое новое сообщение";
- `async with bot` открывает и корректно закрывает HTTP-сессию;
- `start_polling()` запускает long polling и на платформах с поддержкой сигналов корректно завершает работу по `SIGINT` / `SIGTERM`.

## Основные понятия

| Сущность | Зачем нужна |
|----------|-------------|
| `Bot` | Вызовы API, polling, lifecycle hooks |
| `Dispatcher` | Роутинг событий к обработчикам |
| Handler | Ваша async-функция, которая реагирует на событие |
| Filter | Дополнительное условие для обработчика |
| `FSMContext` | Состояние и данные конкретного пользователя в конкретном чате |
| Middleware | Общая логика вокруг обработчиков |
| DI | Автоматическая подстановка зависимостей в параметры обработчика |

Поток обработки события выглядит так:

```text
Long polling -> parse_event() -> middleware -> первый подходящий handler -> DI -> callback
```

## Примеры

### Обработка команд

Фильтр команды принимает имя команды без слэша:

```python
from vk_teams_async_bot import Bot, CommandFilter, Dispatcher, NewMessageEvent

dp = Dispatcher()


@dp.message(CommandFilter("start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Привет! Я бот.")


@dp.message(CommandFilter("help"))
async def cmd_help(event: NewMessageEvent, bot: Bot):
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="/start -- запуск\n/help -- справка",
    )
```

`CommandFilter("start")` совпадает с `/start` и `/start аргументы`.

Если нужен более короткий синтаксис, можно использовать `@dp.command("start")`. Это просто сокращение для `@dp.message(CommandFilter("start"))`.

### Инлайн-клавиатура

```python
from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    CommandFilter,
    Dispatcher,
    InlineKeyboardMarkup,
    KeyboardButton,
    NewMessageEvent,
    StyleKeyboard,
)

dp = Dispatcher()


def menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(
            text="Основное",
            callback_data="cb_primary",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="Внимание",
            callback_data="cb_attention",
            style=StyleKeyboard.ATTENTION,
        ),
        KeyboardButton(text="Обычная", callback_data="cb_base"),
        KeyboardButton(text="Документация API", url="https://teams.vk.com/botapi/"),
    )
    return kb


@dp.message(CommandFilter("menu"))
async def show_menu(event: NewMessageEvent, bot: Bot):
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="Выберите действие:",
        inline_keyboard_markup=menu_keyboard(),
    )


@dp.callback_query(CallbackDataFilter("cb_primary"))
async def on_primary(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id, text="Нажато")
    if event.message is None:
        return

    await bot.edit_text(
        chat_id=event.chat.chat_id,
        msg_id=event.message.msg_id,
        text="Вы выбрали: Основное",
        inline_keyboard_markup=menu_keyboard(),
    )
```

Кнопка может содержать либо `callback_data`, либо `url`, но не оба поля сразу.

### Фильтры и их композиция

```python
from vk_teams_async_bot import (
    CallbackDataRegexpFilter,
    CommandFilter,
    FileFilter,
    ForwardFilter,
    MentionFilter,
    RegexpFilter,
    ReplyFilter,
    StickerFilter,
    TagFilter,
    VoiceFilter,
)


@dp.message(CommandFilter("start"))
async def on_start(event, bot): ...


@dp.message(RegexpFilter(r"привет|здравствуй"))
async def on_greeting(event, bot): ...


@dp.message(FileFilter())
async def on_file(event, bot): ...


@dp.message(VoiceFilter())
async def on_voice(event, bot): ...


@dp.message(StickerFilter())
async def on_sticker(event, bot): ...


@dp.message(FileFilter() & ~VoiceFilter())
async def on_file_not_voice(event, bot): ...


@dp.message(RegexpFilter(r"заказ") | CommandFilter("order"))
async def on_order(event, bot): ...


@dp.callback_query(CallbackDataRegexpFilter(r"^item:\d+$"))
async def on_item(event, bot): ...
```

Основные встроенные фильтры:

| Фильтр | Что делает |
|--------|------------|
| `MessageFilter()` | Совпадает с любым новым сообщением |
| `CommandFilter("start")` | Совпадает с командой `/start` |
| `RegexpFilter(pattern)` | Ищет регулярное выражение в тексте сообщения |
| `TagFilter(tags)` | Проверяет точное совпадение текста с одним из значений |
| `CallbackDataFilter(data)` | Проверяет точное совпадение `callback_data` |
| `CallbackDataRegexpFilter(pattern)` | Проверяет `callback_data` по regex |
| `StateFilter(state[, storage])` | Проверяет текущее FSM-состояние |
| `FileFilter()` | Сообщение содержит файл |
| `VoiceFilter()` | Сообщение содержит голосовое сообщение |
| `StickerFilter()` | Сообщение содержит стикер |
| `MentionFilter()` | Сообщение содержит упоминание |
| `ReplyFilter()` | Сообщение является ответом |
| `ForwardFilter()` | Сообщение является пересланным |
| `RegexpTextPartsFilter(pattern)` | Ищет regex в текстовых частях ответа или пересланного сообщения |
| `MessageTextPartFromNickFilter(nick)` | Проверяет ник автора в частях сообщения |
| `&`, `\|`, `~` | Логические комбинации фильтров |

### Форматирование текста

Поддерживаются три подхода:

- обычный текст;
- `parse_mode=ParseMode.MARKDOWNV2`;
- `parse_mode=ParseMode.HTML`.

```python
from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent, ParseMode

dp = Dispatcher()


@dp.message()
async def format_demo(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Обычный текст")

    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="*жирный* _курсив_ __подчеркнутый__",
        parse_mode=ParseMode.MARKDOWNV2,
    )

    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="<b>жирный</b> <i>курсив</i> <u>подчеркнутый</u>",
        parse_mode=ParseMode.HTML,
    )
```

Если нужен точный контроль по диапазонам символов, используйте `Format` и `StyleType`. Полный пример есть в [examples/format_bot.py](examples/format_bot.py).

### FSM: пошаговые сценарии

FSM нужна для сценариев, где бот должен помнить текущий шаг пользователя и накопленные данные.

```python
import asyncio
import os

from vk_teams_async_bot import (
    Bot,
    CommandFilter,
    Dispatcher,
    FSMContext,
    MemoryStorage,
    NewMessageEvent,
    State,
    StateFilter,
    StatesGroup,
)


class OrderForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(bot_token=os.environ["BOT_TOKEN"])


@dp.message(CommandFilter("order"))
async def start_order(
    event: NewMessageEvent,
    bot: Bot,
    fsm_context: FSMContext,
):
    await fsm_context.set_state(OrderForm.waiting_name)
    await bot.send_text(chat_id=event.chat.chat_id, text="Как вас зовут?")


@dp.message(StateFilter(OrderForm.waiting_name, storage))
async def get_name(
    event: NewMessageEvent,
    bot: Bot,
    fsm_context: FSMContext,
):
    await fsm_context.update_data(name=event.text)
    await fsm_context.set_state(OrderForm.waiting_phone)
    await bot.send_text(chat_id=event.chat.chat_id, text="Введите номер телефона:")


@dp.message(StateFilter(OrderForm.waiting_phone, storage))
async def get_phone(
    event: NewMessageEvent,
    bot: Bot,
    fsm_context: FSMContext,
):
    await fsm_context.update_data(phone=event.text)
    data = await fsm_context.get_data()
    await fsm_context.clear()
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text=f"Заказ принят!\nИмя: {data['name']}\nТелефон: {data['phone']}",
    )


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

Основные методы `FSMContext`:

- `set_state(state)` -- установить состояние;
- `get_state()` -- получить текущее состояние;
- `update_data(**kwargs)` -- добавить или обновить данные;
- `get_data()` -- получить словарь данных;
- `clear()` -- очистить состояние и данные.

### Middleware

Middleware нужна для общей логики: логирование, проверка прав, измерение времени, аудит, обогащение `data`.

```python
from vk_teams_async_bot import BaseMiddleware, Bot, Dispatcher

dp = Dispatcher()


class AccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_chats: list[str]):
        self.allowed_chats = allowed_chats

    async def __call__(self, handler, event, data):
        chat = getattr(event, "chat", None)
        if chat and chat.chat_id not in self.allowed_chats:
            bot = data["bot"]
            await bot.send_text(chat_id=chat.chat_id, text="Нет доступа.")
            return
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print(f"-> {event.type}")
        result = await handler(event, data)
        print(f"<- {event.type}")
        return result


dp.add_middleware(AccessMiddleware(["allowed@chat.agent"]))
dp.add_middleware(LoggingMiddleware())
```

В `data` доступны как минимум `bot` и `dispatcher`. Если у `Dispatcher` настроено хранилище, туда также попадает `fsm_context`.

Встроенный `SessionTimeoutMiddleware` очищает FSM-сессии по таймауту:

```python
from vk_teams_async_bot import MemoryStorage, SessionTimeoutMiddleware

storage = MemoryStorage()
session_timeout_mw = SessionTimeoutMiddleware(storage, timeout=300)
dp.add_middleware(session_timeout_mw)
```

Если вы используете `SessionTimeoutMiddleware`, корректно закрывайте его на shutdown:

```python
@bot.on_shutdown
async def shutdown(bot):
    await session_timeout_mw.close()
```

### Работа с файлами

```python
from vk_teams_async_bot import Bot, Dispatcher, FileFilter, NewMessageEvent

dp = Dispatcher()


@dp.message()
async def send_files(event: NewMessageEvent, bot: Bot):
    result = await bot.send_file(
        chat_id=event.chat.chat_id,
        file="photo.jpg",
        caption="Фото с диска",
    )

    await bot.send_file(
        chat_id=event.chat.chat_id,
        file_id=result.file_id,
        caption="Фото с сервера",
    )

    await bot.send_voice(chat_id=event.chat.chat_id, file="audio.ogg")


@dp.message(FileFilter())
async def receive_file(event: NewMessageEvent, bot: Bot):
    for part in event.parts or []:
        if hasattr(part, "payload") and hasattr(part.payload, "file_id"):
            info = await bot.get_file_info(part.payload.file_id)
            data = await bot.download_file(info.url)
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"Получен файл: {info.filename} ({len(data)} байт)",
            )
```

`send_file()` и `send_voice()` умеют работать и с путями к файлам, и с уже известным `file_id`.

### Dependency Injection

Обработчики могут получать зависимости по аннотациям. Поддерживаются:

- обычные функции;
- async-функции;
- async-генераторы с очисткой ресурса.

```python
import aiohttp
from typing import Annotated

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

dp = Dispatcher()
bot = Bot(bot_token="TOKEN")


def get_config():
    return {"max_retries": 3}


async def get_session():
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


bot.depends.extend([get_config, get_session])


@dp.message()
async def handler(
    event: NewMessageEvent,
    bot: Bot,
    config: get_config,
    session: Annotated[aiohttp.ClientSession, get_session],
):
    async with session.get("https://example.com") as resp:
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Status: {resp.status}, retries: {config['max_retries']}",
        )
```

### Хуки жизненного цикла

```python
from vk_teams_async_bot import Bot

bot = Bot(bot_token="TOKEN")


@bot.on_startup
async def on_start(bot: Bot):
    info = await bot.get_self()
    print(f"Бот запущен: {info.first_name} (@{info.nick})")


@bot.on_shutdown
async def on_stop(bot: Bot):
    print("Бот остановлен")
```

Хуки полезны для инициализации ресурсов, прогрева кэша, старта фоновых задач и корректного завершения middleware или соединений.

## Поддерживаемые события

Библиотека типизирует и маршрутизирует такие события:

| Событие | Декоратор |
|---------|-----------|
| `newMessage` | `@dp.message(...)` |
| `editedMessage` | `@dp.edited_message(...)` |
| `deletedMessage` | `@dp.deleted_message(...)` |
| `pinnedMessage` | `@dp.pinned_message(...)` |
| `unpinnedMessage` | `@dp.unpinned_message(...)` |
| `newChatMembers` | `@dp.new_chat_members(...)` |
| `leftChatMembers` | `@dp.left_chat_members(...)` |
| `callbackQuery` | `@dp.callback_query(...)` |

## Реализованные методы API

Библиотека покрывает все 27 эндпоинтов VK Teams Bot API, которые реализованы в версии `1.0.0`.

### Сообщения

| Метод | Эндпоинт | HTTP |
|-------|----------|------|
| `send_text(chat_id, text, ...)` | `/messages/sendText` | GET |
| `send_file(chat_id, file_id=... or file=...)` | `/messages/sendFile` | GET / POST |
| `send_voice(chat_id, file_id=... or file=...)` | `/messages/sendVoice` | GET / POST |
| `edit_text(chat_id, msg_id, text, ...)` | `/messages/editText` | GET |
| `delete_messages(chat_id, msg_id)` | `/messages/deleteMessages` | GET |
| `answer_callback_query(query_id, ...)` | `/messages/answerCallbackQuery` | GET |

### Чаты

> `create_chat()` и `add_chat_members()` требуют on-premise конфигурации и включения private methods у администратора VK Teams.

| Метод | Эндпоинт | HTTP |
|-------|----------|------|
| `create_chat(name, ...)` | `/chats/createChat` | GET |
| `set_chat_avatar(chat_id, image)` | `/chats/avatar/set` | POST |
| `add_chat_members(chat_id, members)` | `/chats/members/add` | GET |
| `delete_chat_members(chat_id, members)` | `/chats/members/delete` | GET |
| `send_chat_actions(chat_id, actions)` | `/chats/sendActions` | GET |
| `get_chat_info(chat_id)` | `/chats/getInfo` | GET |
| `get_chat_admins(chat_id)` | `/chats/getAdmins` | GET |
| `get_chat_members(chat_id, cursor=...)` | `/chats/getMembers` | GET |
| `get_blocked_users(chat_id)` | `/chats/getBlockedUsers` | GET |
| `get_pending_users(chat_id)` | `/chats/getPendingUsers` | GET |
| `block_user(chat_id, user_id, ...)` | `/chats/blockUser` | GET |
| `unblock_user(chat_id, user_id)` | `/chats/unblockUser` | GET |
| `resolve_pending(chat_id, approve, ...)` | `/chats/resolvePending` | GET |
| `set_chat_title(chat_id, title)` | `/chats/setTitle` | GET |
| `set_chat_about(chat_id, about)` | `/chats/setAbout` | GET |
| `set_chat_rules(chat_id, rules)` | `/chats/setRules` | GET |
| `pin_message(chat_id, msg_id)` | `/chats/pinMessage` | GET |
| `unpin_message(chat_id, msg_id)` | `/chats/unpinMessage` | GET |

### Файлы и сервисные методы

| Метод | Что делает | HTTP |
|-------|------------|------|
| `get_file_info(file_id)` | Получает метаданные файла | GET |
| `get_self()` | Возвращает информацию о боте | GET |
| `get_events(last_event_id, poll_time)` | Получает события long polling | GET |
| `download_file(url)` | Скачивает файл по URL из `FileInfo` | helper method |

## Обработка ошибок и retry

Библиотека предоставляет иерархию исключений:

```python
from vk_teams_async_bot import (
    APIError,
    EventParsingError,
    NetworkError,
    PollingError,
    RateLimitError,
    ServerError,
    SessionError,
    TimeoutError,
    VKTeamsError,
)
```

Что важно понимать:

- `VKTeamsError` -- базовый класс, если нужен общий `except`;
- HTTP-клиент автоматически поднимает `APIError`, `RateLimitError`, `ServerError`, `NetworkError` и `TimeoutError`;
- `APIError` покрывает ошибки API и ответы вида `ok=false`;
- `EventParsingError` относится к разбору сырых событий через `parse_event()`. Внутри `get_events()` такие ошибки логируются, а проблемное событие превращается в `RawUnknownEvent`;
- `SessionError` и `PollingError` входят в публичную иерархию ошибок и могут пригодиться, если вы строите свою обертку над polling-слоем.

Автоматический retry с экспоненциальным backoff:

```python
from vk_teams_async_bot import Bot
from vk_teams_async_bot.client.retry import RetryPolicy

bot = Bot(
    bot_token="TOKEN",
    retry_policy=RetryPolicy(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        jitter=True,
    ),
)
```

## Примеры в репозитории

Директория [`examples/`](examples/) содержит готовые сценарии:

| Файл | Что показывает |
|------|----------------|
| [`examples/echo_bot.py`](examples/echo_bot.py) | Минимальный эхо-бот |
| [`examples/start_bot.py`](examples/start_bot.py) | Обработку команды `/start` |
| [`examples/callback_keyboard_bot.py`](examples/callback_keyboard_bot.py) | Меню с callback-кнопками и переходами между экранами |
| [`examples/format_bot.py`](examples/format_bot.py) | Обычный текст, MarkdownV2, HTML и Format API |
| [`examples/middleware_bot.py`](examples/middleware_bot.py) | Middleware для контроля доступа |
| [`examples/send_audio.py`](examples/send_audio.py) | Отправку файлов и повторную отправку по `file_id` |
| [`examples/depends.py`](examples/depends.py) | Dependency injection |
| [`examples/showcase_bot/`](examples/showcase_bot/) | Полный демонстрационный бот со всеми основными возможностями |

Если вы только знакомитесь с проектом, лучше начать с `echo_bot.py`, потом перейти к `callback_keyboard_bot.py`, а затем посмотреть `showcase_bot/`.

## Как устроен проект

Ключевые части библиотеки:

- `vk_teams_async_bot/bot.py` -- `Bot`, lifecycle hooks, polling.
- `vk_teams_async_bot/dispatcher.py` -- диспетчер и декораторы обработчиков.
- `vk_teams_async_bot/methods/` -- реализация методов API.
- `vk_teams_async_bot/types/` -- Pydantic-модели событий, файлов, чатов, ответов и перечислений.
- `vk_teams_async_bot/filters/` -- фильтры сообщений, callback'ов, состояний и частей сообщений.
- `vk_teams_async_bot/fsm/` -- состояния, контекст и хранилища.
- `vk_teams_async_bot/middleware/` -- базовый middleware, менеджер цепочки, таймаут сессий.
- `tests/unit/` и `tests/integration/` -- unit и integration tests.

## Локальная разработка

Установка зависимостей для разработки:

```bash
poetry install --with dev
```

Запуск тестов:

```bash
poetry run pytest
```

По умолчанию этот запуск не включает `live`-тесты. Они требуют отдельного `.env.test` с реальными параметрами VK Teams API.

При необходимости отдельно:

```bash
poetry run mypy vk_teams_async_bot
poetry run pyright
```

## Миграция с 0.2.x

Версия `1.0.0` содержит архитектурные изменения. Подробности и примеры "до / после" смотрите в [MIGRATION.md](MIGRATION.md).

## Лицензия

[MIT](LICENSE) -- Smirnov Aleksandr (Quakeer444)
