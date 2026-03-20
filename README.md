[![PyPI Version](https://img.shields.io/pypi/v/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![Python](https://img.shields.io/pypi/pyversions/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://github.com/Quakeer444/vk_teams_async_bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Quakeer444/vk_teams_async_bot/actions)

# vk-teams-async-bot

Асинхронный Python-фреймворк для создания ботов [VK Teams](https://teams.vk.com/).

## Возможности

- **27 методов API** -- полное покрытие VK Teams Bot API
- **Event-driven архитектура** -- long polling, dispatcher, декораторы, фильтры
- **FSM** -- конечный автомат для многошаговых диалогов
- **Middleware** -- хуки до и после обработчика
- **Dependency Injection** -- автоматическое разрешение параметров обработчика]
- **[Showcase-бот](examples/showcase_bot/)** -- готовый бот-пример, демонстрирующий основные возможности фреймворка: фильтры, FSM, middleware, DI, клавиатуры, пагинации, работу с файлами и чатами
- **Retry** -- экспоненциальный backoff с jitter

## Установка

Требуется Python 3.11+.

```bash
pip install vk-teams-async-bot
```

## Быстрый старт

1. Получите токен бота у [Метабота](https://teams.vk.com/profile/70001).
2. Создайте файл `bot.py`:

```python
import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
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

3. Запустите:

```bash
export BOT_TOKEN="ваш_токен"
python bot.py
```

On-premise: передайте параметр `url=` в `Bot(...)`, если используете собственный API-эндпоинт.

## Использование

### Команды

```python
from vk_teams_async_bot import Bot, CommandFilter, Dispatcher, NewMessageEvent

dp = Dispatcher()


@dp.message(CommandFilter("start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Привет!")


# Сокращённая запись:
@dp.command("help")
async def cmd_help(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="/start -- запуск\n/help -- помощь")
```

`CommandFilter("start")` срабатывает на `/start` и `/start аргументы`. Слеш в аргументе не указывается.

### Inline-клавиатура

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


@dp.message(CommandFilter("menu"))
async def show_menu(event: NewMessageEvent, bot: Bot):
    kb = InlineKeyboardMarkup(buttons_in_row=2)
    kb.add(
        KeyboardButton(text="OK", callback_data="ok", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Docs", url="https://teams.vk.com/botapi/"),
    )
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="Выберите:",
        inline_keyboard_markup=kb,
    )


@dp.callback_query(CallbackDataFilter("ok"))
async def on_ok(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id, text="Нажато")
```

Кнопка может содержать либо `callback_data`, либо `url`, но не оба одновременно.

### Фильтры

Фильтры можно комбинировать с помощью `&`, `|`, `~`:

```python
from vk_teams_async_bot import (
    CommandFilter,
    FileFilter,
    RegexpFilter,
    VoiceFilter,
)

# файл, но не голосовое сообщение
@dp.message(FileFilter() & ~VoiceFilter())
async def on_file(event, bot): ...

# regex или команда
@dp.message(RegexpFilter(r"order") | CommandFilter("order"))
async def on_order(event, bot): ...
```

**Встроенные фильтры:**

| Фильтр | Описание |
|--------|----------|
| `MessageFilter()` | Любое новое сообщение |
| `TextFilter()` | Непустой текст |
| `CommandFilter("cmd")` | Команда `/cmd` |
| `RegexpFilter(pattern)` | Совпадение по регулярному выражению |
| `TagFilter(tags)` | Точное совпадение текста |
| `ChatTypeFilter(ChatType.PRIVATE)` | По типу чата |
| `ChatIdFilter("id")` | По ID чата |
| `FromUserFilter("id")` | По отправителю |
| `CallbackDataFilter(data)` | Точное совпадение callback data |
| `CallbackDataRegexpFilter(pattern)` | Regex по callback data |
| `StateFilter(state, storage)` | Состояние FSM |
| `FileFilter()` | Есть вложенный файл |
| `FileTypeFilter("image")` | Файл по типу |
| `VoiceFilter()` | Голосовое сообщение |
| `StickerFilter()` | Стикер |
| `MentionFilter()` | Любое упоминание |
| `MentionUserFilter("id")` | Упоминание конкретного пользователя |
| `ReplyFilter()` | Ответ на сообщение |
| `ForwardFilter()` | Пересланное сообщение |
| `RegexpTextPartsFilter(pattern)` | Regex по текстовым частям сообщения |
| `MessageTextPartFromNickFilter(nick, text)` | Упоминание по нику + совпадение текста |

Для создания собственного фильтра наследуйтесь от `FilterBase`:

```python
from vk_teams_async_bot import FilterBase, NewMessageEvent


class LongMessageFilter(FilterBase):
    def __init__(self, min_length: int = 100):
        self.min_length = min_length

    def __call__(self, event):
        if isinstance(event, NewMessageEvent) and event.text:
            return len(event.text) >= self.min_length
        return False


@dp.message(LongMessageFilter(200))
async def on_long(event, bot): ...
```

### FSM (конечный автомат)

Многошаговые диалоги с per-user состоянием, привязанным к `(chat_id, user_id)`:

```python
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


class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(CommandFilter("order"))
async def start(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
    await fsm_context.set_state(Form.waiting_name)
    await bot.send_text(chat_id=event.chat.chat_id, text="Ваше имя?")


@dp.message(StateFilter(Form.waiting_name, storage))
async def get_name(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
    await fsm_context.update_data(name=event.text)
    await fsm_context.set_state(Form.waiting_phone)
    await bot.send_text(chat_id=event.chat.chat_id, text="Ваш телефон?")


@dp.message(StateFilter(Form.waiting_phone, storage))
async def get_phone(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
    await fsm_context.update_data(phone=event.text)
    data = await fsm_context.get_data()
    await fsm_context.clear()
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text=f"Готово! Имя: {data['name']}, Телефон: {data['phone']}",
    )
```

Методы `FSMContext`: `set_state()`, `get_state()`, `update_data()`, `get_data()`, `clear()`.

`MemoryStorage` предназначен для разработки. Для продакшена реализуйте `BaseStorage` поверх Redis или базы данных:

```python
import json

import redis.asyncio as redis

from vk_teams_async_bot import BaseStorage, StorageKey


class RedisStorage(BaseStorage):
    def __init__(self, url: str = "redis://localhost:6379"):
        self._redis = redis.from_url(url)

    async def get_state(self, key: StorageKey) -> str | None:
        return await self._redis.get(f"state:{key[0]}:{key[1]}")

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        k = f"state:{key[0]}:{key[1]}"
        if state is None:
            await self._redis.delete(k)
        else:
            await self._redis.set(k, state)

    async def get_data(self, key: StorageKey) -> dict:
        raw = await self._redis.get(f"data:{key[0]}:{key[1]}")
        return json.loads(raw) if raw else {}

    async def set_data(self, key: StorageKey, data: dict) -> None:
        await self._redis.set(f"data:{key[0]}:{key[1]}", json.dumps(data))

    async def close(self) -> None:
        await self._redis.aclose()
```

### Middleware

```python
from vk_teams_async_bot import BaseMiddleware, Bot, Dispatcher

dp = Dispatcher()


class LogMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print(f"-> {event.type}")
        result = await handler(event, data)
        print(f"<- {event.type}")
        return result


dp.add_middleware(LogMiddleware())
```

Словарь `data` содержит `bot`, `dispatcher` и `fsm_context` (если настроено хранилище).

Встроенный `SessionTimeoutMiddleware` очищает устаревшие FSM-сессии:

```python
from vk_teams_async_bot import MemoryStorage, SessionTimeoutMiddleware

storage = MemoryStorage()
mw = SessionTimeoutMiddleware(storage, timeout=300)
dp.add_middleware(mw)


@bot.on_shutdown
async def shutdown(bot):
    await mw.close()
```

### Файлы

```python
# Отправить файл с диска
result = await bot.send_file(chat_id=chat_id, file="photo.jpg", caption="Фото")

# Переслать по file_id
await bot.send_file(chat_id=chat_id, file_id=result.file_id)

# Отправить голосовое сообщение
await bot.send_voice(chat_id=chat_id, file="audio.ogg")

# Скачать файл
info = await bot.get_file_info(file_id)
data = await bot.download_file(info.url)
```

### Dependency Injection

Зарегистрируйте фабрики в `bot.depends` и используйте аннотации типов в обработчиках:

```python
from typing import Annotated
from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

dp = Dispatcher()
bot = Bot(bot_token="TOKEN")


def get_config():
    return {"debug": True}


async def get_db():
    conn = await create_connection()
    try:
        yield conn
    finally:
        await conn.close()


bot.depends.extend([get_config, get_db])


@dp.message()
async def handler(
    event: NewMessageEvent,
    bot: Bot,
    config: get_config,
    db: Annotated[Connection, get_db],
):
    ...
```

Поддерживаются: синхронные функции, асинхронные функции, асинхронные генераторы (с очисткой ресурсов).

### Lifecycle-хуки

```python
@bot.on_startup
async def on_start(bot: Bot):
    info = await bot.get_self()
    print(f"Бот запущен: {info.first_name} (@{info.nick})")


@bot.on_shutdown
async def on_stop(bot: Bot):
    print("Бот остановлен")
```

### Форматирование текста

```python
from vk_teams_async_bot import ParseMode

# Markdown
await bot.send_text(chat_id=chat_id, text="*жирный* _курсив_", parse_mode=ParseMode.MARKDOWNV2)

# HTML
await bot.send_text(chat_id=chat_id, text="<b>жирный</b> <i>курсив</i>", parse_mode=ParseMode.HTML)
```

Для inline-форматирования используйте `Format` и `StyleType` -- см. [examples/format_bot.py](examples/format_bot.py).

## События

| Событие | Декоратор |
|---------|-----------|
| `newMessage` | `@dp.message()` |
| `editedMessage` | `@dp.edited_message()` |
| `deletedMessage` | `@dp.deleted_message()` |
| `pinnedMessage` | `@dp.pinned_message()` |
| `unpinnedMessage` | `@dp.unpinned_message()` |
| `newChatMembers` | `@dp.new_chat_members()` |
| `leftChatMembers` | `@dp.left_chat_members()` |
| `callbackQuery` | `@dp.callback_query()` |

Неизвестные типы событий парсятся как `RawUnknownEvent` и пропускаются без ошибок.

## Методы API

### Сообщения

| Метод | Endpoint |
|-------|----------|
| `send_text(chat_id, text, ...)` | `/messages/sendText` |
| `send_file(chat_id, file=... \| file_id=...)` | `/messages/sendFile` |
| `send_voice(chat_id, file=... \| file_id=...)` | `/messages/sendVoice` |
| `edit_text(chat_id, msg_id, text, ...)` | `/messages/editText` |
| `delete_messages(chat_id, msg_id)` | `/messages/deleteMessages` |
| `answer_callback_query(query_id, ...)` | `/messages/answerCallbackQuery` |

### Чаты

| Метод | Endpoint |
|-------|----------|
| `get_chat_info(chat_id)` | `/chats/getInfo` |
| `get_chat_admins(chat_id)` | `/chats/getAdmins` |
| `get_chat_members(chat_id, cursor=...)` | `/chats/getMembers` |
| `get_blocked_users(chat_id)` | `/chats/getBlockedUsers` |
| `get_pending_users(chat_id)` | `/chats/getPendingUsers` |
| `block_user(chat_id, user_id, ...)` | `/chats/blockUser` |
| `unblock_user(chat_id, user_id)` | `/chats/unblockUser` |
| `resolve_pending(chat_id, approve, ...)` | `/chats/resolvePending` |
| `set_chat_title(chat_id, title)` | `/chats/setTitle` |
| `set_chat_about(chat_id, about)` | `/chats/setAbout` |
| `set_chat_rules(chat_id, rules)` | `/chats/setRules` |
| `pin_message(chat_id, msg_id)` | `/chats/pinMessage` |
| `unpin_message(chat_id, msg_id)` | `/chats/unpinMessage` |
| `send_chat_actions(chat_id, actions)` | `/chats/sendActions` |
| `set_chat_avatar(chat_id, image)` | `/chats/avatar/set` |
| `create_chat(name, ...)` | `/chats/createChat` * |
| `add_chat_members(chat_id, members)` | `/chats/members/add` * |
| `delete_chat_members(chat_id, members)` | `/chats/members/delete` |

\* Только для on-premise, требуется настройка администратором.

### Файлы и сервис

| Метод | Описание |
|-------|----------|
| `get_file_info(file_id)` | Метаданные файла |
| `download_file(url)` | Скачать файл по URL |
| `get_self()` | Информация о боте |
| `get_events(last_event_id, poll_time)` | Long polling |

## Обработка ошибок

```python
from vk_teams_async_bot import VKTeamsError, APIError, RateLimitError, ServerError, NetworkError, TimeoutError
```

Иерархия:

```
VKTeamsError
  +-- APIError
  |     +-- RateLimitError
  +-- ServerError
  +-- NetworkError
  +-- TimeoutError
  +-- SessionError
  +-- PollingError
  +-- EventParsingError
```

Автоматический retry с экспоненциальным backoff:

```python
from vk_teams_async_bot import Bot
from vk_teams_async_bot.client.retry import RetryPolicy

bot = Bot(
    bot_token="TOKEN",
    retry_policy=RetryPolicy(max_retries=3, base_delay=1.0, max_delay=30.0, jitter=True),
)
```

## Конфигурация бота

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `bot_token` | -- | Токен бота (обязательный) |
| `url` | `https://api.internal.myteam.mail.ru` | Базовый URL API |
| `base_path` | `/bot/v1` | Базовый путь API |
| `timeout` | `30` | Таймаут HTTP-запроса (секунды) |
| `poll_time` | `15` | Таймаут long polling (секунды) |
| `last_event_id` | `0` | Начальный ID события для polling |
| `max_concurrent_handlers` | `100` | Максимум параллельных обработчиков |
| `shutdown_timeout` | `30.0` | Таймаут graceful shutdown (секунды) |
| `max_download_size` | `100 MB` | Максимальный размер скачиваемого файла |
| `retry_policy` | `None` | `RetryPolicy` для автоматических повторов |
| `ssl` | `None` | Пользовательская конфигурация SSL |

## Примеры

В директории [`examples/`](examples/) находятся готовые к запуску боты:

| Пример | Что демонстрирует |
|--------|-------------------|
| [`echo_bot.py`](examples/echo_bot.py) | Минимальный echo-бот |
| [`start_bot.py`](examples/start_bot.py) | Обработка команды `/start` |
| [`callback_keyboard_bot.py`](examples/callback_keyboard_bot.py) | Inline-кнопки, навигация по экранам |
| [`format_bot.py`](examples/format_bot.py) | MarkdownV2, HTML, Format API |
| [`middleware_bot.py`](examples/middleware_bot.py) | Middleware для контроля доступа |
| [`send_audio.py`](examples/send_audio.py) | Загрузка файла, повторная отправка по `file_id` |
| [`depends.py`](examples/depends.py) | Dependency injection |
| [`showcase_bot/`](examples/showcase_bot/) | Полная демонстрация: все возможности вместе |

Начните с `echo_bot.py`, затем `callback_keyboard_bot.py`, далее изучите `showcase_bot/`.

## Структура проекта

```
vk_teams_async_bot/
  bot.py            -- Bot, lifecycle-хуки, polling
  dispatcher.py     -- Маршрутизация событий, регистрация обработчиков
  methods/          -- Реализация методов API
  types/            -- Pydantic-модели (события, чаты, файлы, клавиатура, ответы)
  filters/          -- Классы фильтров с композицией & | ~
  handlers/         -- Классы обработчиков по типам событий
  fsm/              -- State, StatesGroup, FSMContext, хранилище
  middleware/        -- BaseMiddleware, MiddlewareManager, SessionTimeout
  client/           -- HTTP-сессия, retry policy
```

## Разработка

```bash
# Установка dev-зависимостей
poetry install --with dev

# Запуск тестов
poetry run pytest

# Проверка типов
poetry run mypy vk_teams_async_bot
poetry run pyright
```

Для live-тестов необходим файл `.env.test` с реальными учётными данными VK Teams API.

## Миграция с 0.2.x

Подробное руководство по обновлению с примерами "до/после" -- см. [MIGRATION.md](MIGRATION.md).

Ключевые изменения в 1.0.0:
- Все импорты из верхнеуровневого `vk_teams_async_bot`
- `Bot` -- контекстный менеджер; `start_polling()` принимает `Dispatcher`
- Типизированные Pydantic-события вместо dict-обёрток
- Новая система фильтров с операторами композиции
- `FSMContext` + `MemoryStorage` вместо `DictUserState`
- `BaseMiddleware` с протоколом `__call__(handler, event, data)`

## Важные замечания

- Только long polling (webhook не поддерживается).
- `Dispatcher` вызывает только **первый** подходящий обработчик для каждого события.
- События обрабатываются параллельно (лимит: `max_concurrent_handlers`). События с одинаковым `(chat_id, user_id)` сериализуются автоматически при подключённом FSM-хранилище.
- `MemoryStorage` только для разработки. Для продакшена реализуйте `BaseStorage`.
- `create_chat()` и `add_chat_members()` требуют on-premise VK Teams с настройкой администратора.

## Лицензия

[MIT](LICENSE) -- Смирнов Александр (Quakeer444)
