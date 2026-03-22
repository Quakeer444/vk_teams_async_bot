[![PyPI Version](https://img.shields.io/pypi/v/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![Python](https://img.shields.io/pypi/pyversions/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://github.com/Quakeer444/vk_teams_async_bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Quakeer444/vk_teams_async_bot/actions)

# vk-teams-async-bot

Асинхронный Python-фреймворк для создания ботов [VK Teams](https://teams.vk.com/).

## Возможности

- **28 методов API** - полное покрытие VK Teams Bot API
- **Event-driven архитектура** - long polling, dispatcher, декораторы, фильтры
- **FSM** - конечный автомат для многошаговых диалогов (`MemoryStorage` для простых сценариев, `RedisStorage` для масштабируемых и отказоустойчивых)
- **Middleware** - хуки до и после обработчика
- **Dependency Injection** - автоматическое разрешение параметров обработчика]
- **[Showcase-бот](examples/showcase_bot/)** - готовый бот-пример, демонстрирующий основные возможности фреймворка: фильтры, FSM, middleware, DI, клавиатуры, пагинации, работу с файлами и чатами
- **Retry** - экспоненциальный backoff с jitter
- **Scheduled-уведомления** - автоматическая отправка сообщений пользователям и группам по расписанию (asyncio-задачи, APScheduler)
- **Rate limiting** - встроенный retry при HTTP 429, throttle-middleware, распределённый rate limiter через Redis с per-user/per-group квотами
- **[Context7 MCP](https://context7.com/quakeer444/vk_teams_async_bot)** - библиотека доступна в Context7, AI-агенты (Claude Code, Cursor, Windsurf и др.) могут подтягивать актуальную документацию автоматически

## Установка

Требуется Python 3.11+.

```bash
pip install vk-teams-async-bot

# С поддержкой Redis (для хранения FSM-состояний):
pip install vk-teams-async-bot[redis]
```

## Быстрый старт

1. Получите токен бота у [Метабота](https://teams.vk.com/profile/70001).
2. Узнайте адрес сервера. Для on-premise адрес сервера уникален для каждой инсталляции - отправьте Метаботу команду `/start` и найдите его в настройках вашего сервера. Пример: `https://myteam.mail.ru`.
3. Создайте файл `bot.py`:

```python
import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

bot = Bot(
    bot_token=os.environ["BOT_TOKEN"],
    url=os.environ.get("BOT_API_URL"),
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

4. Запустите:

```bash
export BOT_TOKEN="ваш_токен"
export BOT_API_URL="https://myteam.mail.ru"  # для on-premise
python bot.py
```

## Содержание

- [Использование](#использование)
  - [Команды](#команды)
  - [Inline-клавиатура](#inline-клавиатура)
  - [Фильтры](#фильтры)
  - [FSM (конечный автомат)](#fsm-конечный-автомат)
    - [RedisStorage для production](#redisstorage-для-production)
  - [Middleware](#middleware)
    - [Middleware для авторизации (RBAC)](#middleware-для-авторизации-rbac)
  - [Файлы](#файлы)
  - [Dependency Injection](#dependency-injection)
  - [Lifecycle-хуки](#lifecycle-хуки)
  - [Форматирование текста](#форматирование-текста)
  - [Расширенные возможности клавиатуры](#расширенные-возможности-клавиатуры)
  - [Перечисления](#перечисления)
- [События](#события)
  - [Базовые модели](#базовые-модели)
  - [Модели событий](#модели-событий)
  - [Типы вложений (MessagePart)](#типы-вложений-messagepart)
- [Методы API](#методы-api)
  - [Сообщения](#сообщения)
  - [Чаты](#чаты)
  - [Файлы и сервис](#файлы-и-сервис)
  - [Модели ответов API](#модели-ответов-api)
  - [Полные сигнатуры ключевых методов](#полные-сигнатуры-ключевых-методов)
- [Обработка ошибок](#обработка-ошибок)
  - [Retry с экспоненциальным backoff](#retry-с-экспоненциальным-backoff)
- [Конфигурация бота](#конфигурация-бота)
- [Автоматические уведомления по расписанию](#автоматические-уведомления-по-расписанию)
  - [Простые периодические уведомления](#простые-периодические-уведомления)
  - [Расписание с APScheduler](#расписание-с-apscheduler)
  - [Управление списком получателей через Redis](#управление-списком-получателей-через-redis)
- [Rate Limiting и защита от злоупотреблений](#rate-limiting-и-защита-от-злоупотреблений)
  - [Встроенный retry при rate limit](#встроенный-retry-при-rate-limit)
  - [Middleware для throttling входящих событий](#middleware-для-throttling-входящих-событий)
  - [Распределённый rate limiting с Redis](#распределённый-rate-limiting-с-redis)
  - [Комбинация: несколько инстансов с общим Redis](#комбинация-несколько-инстансов-с-общим-redis)
- [Примеры](#примеры)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Миграция с 0.2.x](#миграция-с-02x)
- [Важные замечания](#важные-замечания)
- [Лицензия](#лицензия)

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
    await bot.send_text(chat_id=event.chat.chat_id, text="/start - запуск\n/help - помощь")
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

| Фильтр                                      | Описание                               |
| ------------------------------------------- | -------------------------------------- |
| `MessageFilter()`                           | Любое новое сообщение                  |
| `TextFilter()`                              | Непустой текст                         |
| `CommandFilter("cmd")`                      | Команда `/cmd`                         |
| `RegexpFilter(pattern)`                     | Совпадение по регулярному выражению    |
| `TagFilter(tags)`                           | Точное совпадение текста               |
| `ChatTypeFilter(ChatType.PRIVATE)`          | По типу чата                           |
| `ChatIdFilter("id")`                        | По ID чата                             |
| `FromUserFilter("id")`                      | По отправителю                         |
| `CallbackDataFilter(data)`                  | Точное совпадение callback data        |
| `CallbackDataRegexpFilter(pattern)`         | Regex по callback data                 |
| `StateFilter(state, storage)`               | Состояние FSM                          |
| `StateFilter("*")`                          | Любое ненулевое состояние FSM          |
| `StateFilter(None)`                         | Пользователь не в FSM                  |
| `StatesGroupFilter(Group)`                  | Любое состояние из группы              |
| `FileFilter()`                              | Есть вложенный файл                    |
| `FileTypeFilter("image")`                   | Файл по типу                           |
| `VoiceFilter()`                             | Голосовое сообщение                    |
| `StickerFilter()`                           | Стикер                                 |
| `MentionFilter()`                           | Любое упоминание                       |
| `MentionUserFilter("id")`                   | Упоминание конкретного пользователя    |
| `ReplyFilter()`                             | Ответ на сообщение                     |
| `ForwardFilter()`                           | Пересланное сообщение                  |
| `RegexpTextPartsFilter(pattern)`            | Regex по текстовым частям сообщения    |
| `MessageTextPartFromNickFilter(nick, all_text_parts_from_nick=False)` | Пересланные/ответы от конкретного ника |

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

**Wildcard и групповые фильтры:**

```python
from vk_teams_async_bot import StateFilter, StatesGroupFilter

# Любое ненулевое состояние (пользователь "где-то" в FSM):
@dp.message(StateFilter("*"))
async def any_state_handler(event, bot, fsm_context): ...

# Пользователь не в FSM (начальное/сброшенное состояние):
@dp.message(StateFilter(None))
async def no_state_handler(event, bot): ...

# Любое состояние из группы Form:
@dp.message(StatesGroupFilter(Form))
async def form_handler(event, bot, fsm_context): ...
```

`MemoryStorage` хранит данные в памяти процесса - подходит для простых ботов и прототипов. Для масштабируемых и отказоустойчивых решений используйте `RedisStorage` (`pip install vk-teams-async-bot[redis]`):

```python
from vk_teams_async_bot import RedisStorage

# По URL (RedisStorage создаёт и закрывает соединение сам):
storage = RedisStorage(redis_url="redis://localhost:6379/0", state_ttl=600)

# Или с существующим подключением (вы управляете его жизненным циклом):
from redis.asyncio import Redis
redis = Redis.from_url("redis://localhost:6379/0")
storage = RedisStorage(redis=redis, state_ttl=600)

dp = Dispatcher(storage=storage)
```

**Параметры `RedisStorage`:**

- `redis_url` / `redis` - подключение к Redis (нужен один из двух)
- `key_prefix` - префикс ключей (по умолчанию `"vkbot"`)
- `state_ttl` - TTL в секундах (sliding window: обновляется при каждом взаимодействии). `None` - без TTL

`SessionTimeoutMiddleware` **не нужен** при использовании `RedisStorage(state_ttl=...)` - Redis автоматически удаляет просроченные сессии.

#### RedisStorage для production

Для промышленной эксплуатации, когда состояния FSM должны сохраняться между перезапусками бота и распределяться между инстансами:

```python
import asyncio
import os

from redis.asyncio import Redis

from vk_teams_async_bot import Bot, Dispatcher, RedisStorage

# 1. Подключение по URL (RedisStorage создаёт и закрывает соединение сам)
storage = RedisStorage(
    redis_url="redis://localhost:6379/0",
    key_prefix="mybot",   # уникальный префикс, если несколько ботов на одном Redis
    state_ttl=3600,        # TTL сессии: 1 час (sliding window)
)

# 2. С существующим Redis-клиентом (вы управляете жизненным циклом)
redis = Redis.from_url(
    "redis://localhost:6379/0",
    decode_responses=False,
    max_connections=20,     # пул соединений
)
storage = RedisStorage(redis=redis, key_prefix="mybot", state_ttl=3600)

# 3. Redis Sentinel (высокая доступность)
from redis.asyncio.sentinel import Sentinel
sentinel = Sentinel(
    [("sentinel1", 26379), ("sentinel2", 26379), ("sentinel3", 26379)],
    socket_timeout=0.5,
)
redis = sentinel.master_for("mymaster")
storage = RedisStorage(redis=redis, key_prefix="mybot", state_ttl=3600)

bot = Bot(bot_token=os.environ["BOT_TOKEN"], url=os.environ.get("BOT_API_URL"))
dp = Dispatcher(storage=storage)


@bot.on_shutdown
async def cleanup(bot: Bot):
    await storage.close()   # закрывает Redis, если RedisStorage им владеет
    # при использовании внешнего redis: await redis.aclose()


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

**Структура ключей в Redis:**

```
{key_prefix}:{chat_id}:{user_id}   # Redis hash
  state → "Form:waiting_name"       # текущее состояние FSM
  data  → '{"name": "Ivan"}'        # данные пользователя (JSON)
```

**Поведение TTL (sliding window):** каждая операция (`get_state`, `set_state`, `get_data`, `set_data`, `update_data`) обновляет TTL ключа. Если пользователь не взаимодействует с ботом дольше `state_ttl` секунд, Redis автоматически удаляет ключ и состояние сбрасывается.

**Несколько инстансов бота:** все инстансы подключаются к одному Redis с одинаковым `key_prefix`. Пользователь может начать диалог с одним инстансом и продолжить с другим - состояние FSM будет единым. Dispatcher автоматически блокирует параллельные события одного пользователя через per-user lock.

Для других бэкендов реализуйте `BaseStorage`.

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

#### Middleware для авторизации (RBAC)

Контроль доступа на основе ролей с учётом FSM-состояния и метаданных пользователя:

```python
from vk_teams_async_bot import BaseMiddleware, Bot, Dispatcher, FSMContext

# Роли и разрешения
ROLES: dict[str, set[str]] = {
    "admin": {"manage_users", "view_reports", "configure"},
    "manager": {"view_reports"},
    "user": set(),
}

# Привязка пользователей к ролям (в production - из БД или LDAP)
USER_ROLES: dict[str, str] = {
    "admin@company.com": "admin",
    "manager@company.com": "manager",
}

# Команды, требующие определённых разрешений
COMMAND_PERMISSIONS: dict[str, str] = {
    "/reports": "view_reports",
    "/config": "configure",
    "/ban": "manage_users",
}


class AuthorizationMiddleware(BaseMiddleware):
    """RBAC-middleware: проверяет разрешения перед вызовом обработчика."""

    async def __call__(self, handler, event, data):
        user_id = str(getattr(event, "from_", ""))
        role = USER_ROLES.get(user_id, "user")
        permissions = ROLES.get(role, set())

        # Добавляем роль и разрешения в data для использования в обработчиках
        data["user_role"] = role
        data["user_permissions"] = permissions

        # Проверяем разрешения для команд
        text = getattr(event, "text", "") or ""
        command = text.split()[0] if text.startswith("/") else None

        if command and command in COMMAND_PERMISSIONS:
            required = COMMAND_PERMISSIONS[command]
            if required not in permissions:
                bot: Bot = data["bot"]
                await bot.send_text(
                    chat_id=event.chat.chat_id,
                    text=f"Нет доступа к {command}. Требуется: {required}",
                )
                return None  # блокируем обработчик

        return await handler(event, data)


dp = Dispatcher()
dp.add_middleware(AuthorizationMiddleware())


# В обработчиках доступны роль и разрешения:
@dp.command("reports")
async def show_reports(event, bot: Bot, user_role: str, user_permissions: set):
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text=f"Отчёты (роль: {user_role})",
    )
```

Middleware можно комбинировать — они выполняются в порядке добавления: первый добавленный оборачивает второй, второй оборачивает третий и т.д.

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

Для inline-форматирования без parse_mode используйте `Format` и `StyleType`:

```python
from vk_teams_async_bot import Bot, Format, StyleType

text = "Жирный и ссылка тут"
fmt = Format()
fmt.add(StyleType.BOLD, offset=0, length=6)
fmt.add(StyleType.LINK, offset=9, length=6, url="https://example.com")

await bot.send_text(chat_id=chat_id, text=text, format_=fmt)
```

`format_` и `parse_mode` взаимоисключающие -- используйте только один из них.

### Расширенные возможности клавиатуры

```python
kb = InlineKeyboardMarkup()
kb.row(btn1, btn2, btn3)   # явная строка (игнорирует buttons_in_row)
kb.add(btn4, btn5)          # автоматическая разбивка по buttons_in_row

# Объединение клавиатур
combined = kb1 + kb2         # новая клавиатура со всеми строками
combined = kb + single_btn   # добавить кнопку как отдельную строку
```

### Перечисления

| Enum | Значения |
| ---- | -------- |
| `EventType` | `NEW_MESSAGE`, `EDITED_MESSAGE`, `DELETED_MESSAGE`, `PINNED_MESSAGE`, `UNPINNED_MESSAGE`, `NEW_CHAT_MEMBERS`, `LEFT_CHAT_MEMBERS`, `CALLBACK_QUERY` |
| `ChatType` | `PRIVATE`, `GROUP`, `CHANNEL` |
| `ChatAction` | `TYPING`, `LOOKING` |
| `Parts` | `FILE`, `STICKER`, `MENTION`, `VOICE`, `FORWARD`, `REPLY` |
| `StyleType` | `BOLD`, `ITALIC`, `UNDERLINE`, `STRIKETHROUGH`, `LINK`, `MENTION`, `INLINE_CODE`, `PRE`, `ORDERED_LIST`, `UNORDERED_LIST`, `QUOTE` |
| `ParseMode` | `MARKDOWNV2`, `HTML` |
| `StyleKeyboard` | `BASE`, `PRIMARY`, `ATTENTION` |

## События

| Событие           | Декоратор                 |
| ----------------- | ------------------------- |
| `newMessage`      | `@dp.message()`           |
| `editedMessage`   | `@dp.edited_message()`    |
| `deletedMessage`  | `@dp.deleted_message()`   |
| `pinnedMessage`   | `@dp.pinned_message()`    |
| `unpinnedMessage` | `@dp.unpinned_message()`  |
| `newChatMembers`  | `@dp.new_chat_members()`  |
| `leftChatMembers` | `@dp.left_chat_members()` |
| `callbackQuery`   | `@dp.callback_query()`    |

Неизвестные типы событий парсятся как `RawUnknownEvent` и пропускаются без ошибок.

### Базовые модели

Модели, используемые внутри событий:

**User** -- отправитель сообщения (`event.from_`):

| Поле | Тип | Описание |
| ---- | --- | -------- |
| `user_id` | `str` | ID пользователя (email или UIN) |
| `first_name` | `str \| None` | Имя |
| `last_name` | `str \| None` | Фамилия |
| `nick` | `str \| None` | Никнейм |

**EventChatRef** -- чат события (`event.chat`):

| Поле | Тип | Описание |
| ---- | --- | -------- |
| `chat_id` | `str` | ID чата |
| `type` | `ChatType \| str` | `"private"`, `"group"`, `"channel"` |
| `title` | `str \| None` | Название (для групп/каналов) |

### Модели событий

Все события наследуют `event_id: int` и `type: EventType`.

**NewMessageEvent** (`@dp.message()`):

| Поле | Тип | Описание |
| ---- | --- | -------- |
| `chat` | `EventChatRef` | Чат |
| `from_` | `User` | Отправитель |
| `msg_id` | `str` | ID сообщения |
| `text` | `str \| None` | Текст |
| `format_` | `dict \| None` | Форматирование |
| `timestamp` | `int \| None` | Unix-время |
| `parts` | `list[MessagePart] \| None` | Вложения (файлы, стикеры, упоминания, ...) |

**EditedMessageEvent** -- как `NewMessageEvent` + `edited_timestamp: int | None`, без `parts`.

**DeletedMessageEvent**: `chat`, `msg_id`, `timestamp`.

**PinnedMessageEvent**: `chat`, `from_`, `msg_id`, `text`, `format_`, `timestamp`.

**UnpinnedMessageEvent**: `chat`, `msg_id`, `timestamp`.

**NewChatMembersEvent**: `chat`, `new_members: list[User]`, `added_by: User`.

**LeftChatMembersEvent**: `chat`, `left_members: list[User]`, `removed_by: User`.

**CallbackQueryEvent** (`@dp.callback_query()`):

| Поле | Тип | Описание |
| ---- | --- | -------- |
| `chat` | `EventChatRef \| None` | Чат |
| `from_` | `User` | Кто нажал кнопку |
| `query_id` | `str` | ID запроса (для `answer_callback_query`) |
| `callback_data` | `str` | Данные кнопки |
| `message` | `NestedMessage \| None` | Сообщение, к которому была кнопка |

**RawUnknownEvent**: `event_id: int`, `type: str`, `payload: dict`.

### Типы вложений (MessagePart)

`event.parts` содержит список `MessagePart` -- discriminated union по полю `type`:

| Тип | `type` | `payload` |
| --- | ------ | --------- |
| `FilePart` | `"file"` | `FilePartPayload(file_id, caption, type, format_)` |
| `StickerPart` | `"sticker"` | `StickerPartPayload(file_id)` |
| `MentionPart` | `"mention"` | `User(user_id, first_name, last_name, nick)` |
| `VoicePart` | `"voice"` | `FilePartPayload(file_id, caption, type, format_)` |
| `ForwardPart` | `"forward"` | `ForwardPartPayload(message: NestedMessage)` |
| `ReplyPart` | `"reply"` | `ReplyPartPayload(message: NestedMessage)` |

**NestedMessage** (внутри `ForwardPart`, `ReplyPart`, `CallbackQueryEvent`):

| Поле | Тип |
| ---- | --- |
| `from_` | `User` |
| `msg_id` | `str` |
| `text` | `str \| None` |
| `format_` | `dict \| None` |
| `timestamp` | `int \| None` |
| `chat` | `NestedMessageChat \| None` |

Пример работы с вложениями:

```python
for part in event.parts or []:
    if isinstance(part, FilePart):
        file_id = part.payload.file_id
    elif isinstance(part, ReplyPart):
        original_text = part.payload.message.text
```

## Методы API

### Сообщения

| Метод | Endpoint | Возвращает |
| ----- | -------- | ---------- |
| `send_text(chat_id, text, ...)` | `/messages/sendText` | `MessageResponse` |
| `send_file(chat_id, file=... \| file_id=...)` | `/messages/sendFile` | `FileUploadResponse` |
| `send_voice(chat_id, file=... \| file_id=...)` | `/messages/sendVoice` | `FileUploadResponse` |
| `edit_text(chat_id, msg_id, text, ...)` | `/messages/editText` | `OkResponse` |
| `delete_messages(chat_id, msg_id)` | `/messages/deleteMessages` | `OkResponse` |
| `answer_callback_query(query_id, ...)` | `/messages/answerCallbackQuery` | `OkResponse` |

### Чаты

| Метод | Endpoint | Возвращает |
| ----- | -------- | ---------- |
| `get_chat_info(chat_id)` | `/chats/getInfo` | `ChatInfoPrivate \| ChatInfoGroup \| ChatInfoChannel` |
| `get_chat_admins(chat_id)` | `/chats/getAdmins` | `AdminsResponse` |
| `get_chat_members(chat_id, cursor=...)` | `/chats/getMembers` | `MembersResponse` |
| `get_blocked_users(chat_id)` | `/chats/getBlockedUsers` | `UsersResponse` |
| `get_pending_users(chat_id)` | `/chats/getPendingUsers` | `UsersResponse` |
| `block_user(chat_id, user_id, ...)` | `/chats/blockUser` | `OkResponse` |
| `unblock_user(chat_id, user_id)` | `/chats/unblockUser` | `OkResponse` |
| `resolve_pending(chat_id, approve, ...)` | `/chats/resolvePending` | `OkResponse` |
| `set_chat_title(chat_id, title)` | `/chats/setTitle` | `OkResponse` |
| `set_chat_about(chat_id, about)` | `/chats/setAbout` | `OkResponse` |
| `set_chat_rules(chat_id, rules)` | `/chats/setRules` | `OkResponse` |
| `pin_message(chat_id, msg_id)` | `/chats/pinMessage` | `OkResponse` |
| `unpin_message(chat_id, msg_id)` | `/chats/unpinMessage` | `OkResponse` |
| `send_chat_actions(chat_id, actions)` | `/chats/sendActions` | `OkResponse` |
| `set_chat_avatar(chat_id, image)` | `/chats/avatar/set` | `OkWithDescriptionResponse` |
| `create_chat(name, ...)` | `/chats/createChat` \* | `ChatCreateResponse` |
| `add_chat_members(chat_id, members)` | `/chats/members/add` \* | `PartialSuccessResponse` |
| `delete_chat_members(chat_id, members)` | `/chats/members/delete` | `OkResponse` |

\* Только для on-premise, требуется настройка администратором.

### Файлы и сервис

| Метод | Описание | Возвращает |
| ----- | -------- | ---------- |
| `get_file_info(file_id)` | Метаданные файла | `FileInfo` |
| `download_file(url)` | Скачать файл по URL | `bytes` |
| `get_self()` | Информация о боте | `BotInfo` |
| `get_events(last_event_id, poll_time)` | Long polling | `list[BaseEvent \| RawUnknownEvent]` |

### Модели ответов API

| Модель | Поля | Используется в |
| ------ | ---- | -------------- |
| `MessageResponse` | `ok: bool`, `msg_id: str` | `send_text` |
| `FileUploadResponse` | `ok: bool`, `file_id: str`, `msg_id: str` | `send_file`, `send_voice` |
| `OkResponse` | `ok: bool` | `edit_text`, `delete_messages`, `answer_callback_query`, ... |
| `OkWithDescriptionResponse` | `ok: bool`, `description: str \| None` | `set_chat_avatar` |
| `ChatCreateResponse` | `ok: bool`, `sn: str` | `create_chat` |
| `PartialSuccessResponse` | `ok: bool`, `failures: list[MemberFailure] \| None` | `add_chat_members` |
| `MembersResponse` | `ok: bool`, `members: list[UserAdmin]`, `cursor: str \| None` | `get_chat_members` |
| `AdminsResponse` | `ok: bool`, `admins: list[UserAdmin]` | `get_chat_admins` |
| `UsersResponse` | `ok: bool`, `users: list[UserIdItem]` | `get_blocked_users`, `get_pending_users` |
| `FileInfo` | `type: str`, `size: int`, `filename: str`, `url: str` | `get_file_info` |
| `BotInfo` | `user_id: str`, `nick: str \| None`, `first_name: str \| None`, `about: str \| None`, `photo: list \| None` | `get_self` |

### Полные сигнатуры ключевых методов

```python
# Отправка текста
await bot.send_text(
    chat_id: str,
    text: str,
    *,
    reply_msg_id: str | int | None = None,       # ответ на сообщение
    forward_chat_id: str | None = None,           # пересылка (оба forward_* обязательны)
    forward_msg_id: str | int | None = None,
    inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
    format_: Format | dict | str | None = None,   # взаимоисключающе с parse_mode
    parse_mode: ParseMode | None = None,
) -> MessageResponse

# Отправка файла (file ИЛИ file_id, не оба)
await bot.send_file(
    chat_id: str,
    *,
    file_id: str | None = None,                    # ранее загруженный файл
    file: str | Path | tuple | None = None,        # путь или (filename, file_obj, content_type)
    caption: str | None = None,
    reply_msg_id: str | int | None = None,
    forward_chat_id: str | None = None,
    forward_msg_id: str | int | None = None,
    inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
    format_: Format | dict | str | None = None,
    parse_mode: ParseMode | None = None,
) -> FileUploadResponse

# Отправка голосового (file ИЛИ file_id, без caption/format_/parse_mode)
await bot.send_voice(
    chat_id: str,
    *,
    file_id: str | None = None,
    file: str | Path | tuple | None = None,
    reply_msg_id: str | int | None = None,
    forward_chat_id: str | None = None,
    forward_msg_id: str | int | None = None,
    inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
) -> FileUploadResponse

# Редактирование текста
await bot.edit_text(
    chat_id: str,
    msg_id: str | int,
    text: str,
    *,
    inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
    format_: Format | dict | str | None = None,
    parse_mode: ParseMode | None = None,
) -> OkResponse

# Создание чата (on-premise)
await bot.create_chat(
    name: str,
    *,
    about: str | None = None,
    rules: str | None = None,
    members: list[str] | None = None,
    public: bool | None = None,
    default_role: str | None = None,
    join_moderation: bool | None = None,
) -> ChatCreateResponse
```

## Обработка ошибок

```python
from vk_teams_async_bot import VKTeamsError, APIError, RateLimitError, ServerError, NetworkError, TimeoutError
```

Иерархия:

```
VKTeamsError
  +- APIError
  |     +- ServerError
  |     +- RateLimitError
  +- NetworkError
  +- TimeoutError
  +- SessionError
  +- PollingError
  +- EventParsingError
```

### Retry с экспоненциальным backoff

Все исходящие API-вызовы бота (`send_text`, `send_file`, `get_chat_info` и др.) автоматически повторяются при временных сбоях. Retry настраивается через `RetryPolicy`:

```python
from vk_teams_async_bot import Bot
from vk_teams_async_bot.client.retry import RetryPolicy

bot = Bot(
    bot_token="TOKEN",
    retry_policy=RetryPolicy(
        max_retries=5,      # максимум повторных попыток (по умолчанию 3)
        base_delay=1.0,     # начальная задержка в секундах (по умолчанию 1.0)
        max_delay=30.0,     # максимальная задержка в секундах (по умолчанию 30.0)
        jitter=True,        # случайный разброс задержки (по умолчанию True)
    ),
)
```

**Алгоритм:**

1. При получении retriable-ошибки вычисляется задержка: `delay = min(base_delay * 2^attempt, max_delay)`
2. Если `jitter=True`, задержка рандомизируется: `delay = random(0, delay)` — предотвращает thundering herd
3. Бот ждёт `delay` секунд и повторяет запрос
4. Процесс повторяется до `max_retries` попыток, после чего исключение пробрасывается

**Какие ошибки повторяются автоматически:**

- `RateLimitError` (HTTP 429) — бот читает заголовок `Retry-After` и ждёт указанное время
- `ServerError` (HTTP 5xx) — временная проблема сервера
- `NetworkError` — ошибки соединения (DNS, TCP, SSL)
- `TimeoutError` — таймаут HTTP-запроса

**Ошибки, которые НЕ повторяются:**

- `APIError` (HTTP 4xx, кроме 429) — ошибка в запросе (неверный chat_id, недостаточно прав и т.д.)

**Пример: ручной retry для собственной бизнес-логики:**

```python
from vk_teams_async_bot import Bot, VKTeamsError, NetworkError, ServerError
from vk_teams_async_bot.client.retry import RetryPolicy, exponential_backoff_with_jitter

policy = RetryPolicy(max_retries=3, base_delay=0.5, max_delay=10.0)


async def send_with_retry(bot: Bot, chat_id: str, text: str):
    """Отправка сообщения с ручным retry и логированием."""
    for attempt in range(policy.max_retries + 1):
        try:
            return await bot.send_text(chat_id=chat_id, text=text)
        except (NetworkError, ServerError) as e:
            if attempt == policy.max_retries:
                raise
            delay = await exponential_backoff_with_jitter(policy, attempt)
            print(f"Retry {attempt + 1}/{policy.max_retries}, delay={delay:.1f}s: {e}")
```

## Конфигурация бота

| Параметр                  | По умолчанию | Описание                                  |
| ------------------------- | ------------ | ----------------------------------------- |
| `bot_token`               | -            | Токен бота (обязательный)                 |
| `url`                     | `https://api.internal.myteam.mail.ru` | Базовый URL API (адрес сервера VK Teams)  |
| `base_path`               | `/bot/v1`    | Базовый путь API                          |
| `timeout`                 | `30`         | Таймаут HTTP-запроса (секунды)            |
| `poll_time`               | `15`         | Таймаут long polling (секунды)            |
| `last_event_id`           | `0`          | Начальный ID события для polling          |
| `max_concurrent_handlers` | `100`        | Максимум параллельных обработчиков        |
| `shutdown_timeout`        | `30.0`       | Таймаут graceful shutdown (секунды)       |
| `max_download_size`       | `100 MB`     | Максимальный размер скачиваемого файла    |
| `retry_policy`            | `None`       | `RetryPolicy` для автоматических повторов |
| `ssl`                     | `None`       | Пользовательская конфигурация SSL         |

## Автоматические уведомления по расписанию

Бот поддерживает отправку автоматических сообщений конкретным пользователям или группам через scheduled-задачи. Для этого используются lifecycle-хуки (`@bot.on_startup`) и `asyncio`-задачи.

### Простые периодические уведомления

```python
import asyncio
import os
from datetime import datetime

from vk_teams_async_bot import Bot, Dispatcher

bot = Bot(bot_token=os.environ["BOT_TOKEN"], url=os.environ.get("BOT_API_URL"))
dp = Dispatcher()

# Список целевых чатов/пользователей для уведомлений
NOTIFICATION_TARGETS = [
    "user1@example.com",
    "user2@example.com",
    "group_chat_id_123",
]


async def send_scheduled_notifications(bot: Bot):
    """Фоновая задача: отправляет уведомления каждые 30 минут."""
    while True:
        await asyncio.sleep(30 * 60)  # 30 минут
        for chat_id in NOTIFICATION_TARGETS:
            try:
                await bot.send_text(
                    chat_id=chat_id,
                    text=f"Автоматический отчёт за {datetime.now():%H:%M}",
                )
            except Exception as e:
                print(f"Ошибка отправки в {chat_id}: {e}")


@bot.on_startup
async def start_scheduler(bot: Bot):
    asyncio.create_task(send_scheduled_notifications(bot))


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

### Расписание с APScheduler

Для сложных расписаний (cron-выражения, конкретные даты, интервалы) используйте [APScheduler](https://apscheduler.readthedocs.io/):

```bash
pip install apscheduler
```

```python
import asyncio
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from vk_teams_async_bot import Bot, Dispatcher

bot = Bot(bot_token=os.environ["BOT_TOKEN"], url=os.environ.get("BOT_API_URL"))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# Целевые группы для разных типов уведомлений
DAILY_REPORT_CHATS = ["team_chat_001", "team_chat_002"]
WEEKLY_DIGEST_CHATS = ["managers_chat"]


async def send_daily_report():
    """Ежедневный отчёт в 09:00 по будням."""
    for chat_id in DAILY_REPORT_CHATS:
        await bot.send_text(chat_id=chat_id, text="Доброе утро! Ежедневный отчёт: ...")


async def send_weekly_digest():
    """Еженедельный дайджест в понедельник в 10:00."""
    for chat_id in WEEKLY_DIGEST_CHATS:
        await bot.send_text(chat_id=chat_id, text="Еженедельный дайджест: ...")


async def send_custom_notification(chat_id: str, message: str):
    """Одноразовое отложенное уведомление."""
    await bot.send_text(chat_id=chat_id, text=message)


@bot.on_startup
async def start_scheduler(bot: Bot):
    # Каждый будний день в 09:00
    scheduler.add_job(send_daily_report, CronTrigger(hour=9, minute=0, day_of_week="mon-fri"))
    # Каждый понедельник в 10:00
    scheduler.add_job(send_weekly_digest, CronTrigger(hour=10, minute=0, day_of_week="mon"))
    # Одноразовое уведомление через 5 минут
    scheduler.add_job(
        send_custom_notification,
        "date",
        run_date=datetime.now() + timedelta(minutes=5),
        args=["user@example.com", "Напоминание о встрече"],
    )
    scheduler.start()


@bot.on_shutdown
async def stop_scheduler(bot: Bot):
    scheduler.shutdown(wait=False)


# Команда для динамического добавления уведомлений
@dp.command("remind")
async def cmd_remind(event, bot: Bot):
    """Пользователь может запланировать напоминание: /remind 60 Текст"""
    parts = (event.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await bot.send_text(chat_id=event.chat.chat_id, text="Формат: /remind <минуты> <текст>")
        return
    minutes, text = int(parts[1]), parts[2]
    scheduler.add_job(
        send_custom_notification,
        "date",
        run_date=datetime.now() + timedelta(minutes=minutes),
        args=[event.chat.chat_id, f"Напоминание: {text}"],
    )
    await bot.send_text(chat_id=event.chat.chat_id, text=f"Напомню через {minutes} мин.")
```

### Управление списком получателей через Redis

Для динамического управления подписками на уведомления используйте `RedisStorage` как общее хранилище:

```python
from redis.asyncio import Redis

redis = Redis.from_url("redis://localhost:6379/0")


async def subscribe(chat_id: str, channel: str):
    """Подписать чат на канал уведомлений."""
    await redis.sadd(f"notify:{channel}", chat_id)


async def unsubscribe(chat_id: str, channel: str):
    """Отписать чат от канала уведомлений."""
    await redis.srem(f"notify:{channel}", chat_id)


async def get_subscribers(channel: str) -> list[str]:
    """Получить всех подписчиков канала."""
    members = await redis.smembers(f"notify:{channel}")
    return [m.decode() for m in members]


async def broadcast(bot: Bot, channel: str, text: str):
    """Отправить сообщение всем подписчикам канала."""
    subscribers = await get_subscribers(channel)
    for chat_id in subscribers:
        try:
            await bot.send_text(chat_id=chat_id, text=text)
        except Exception:
            pass  # пользователь заблокировал бота или покинул чат


@dp.command("subscribe")
async def cmd_subscribe(event, bot: Bot):
    await subscribe(event.chat.chat_id, "daily_reports")
    await bot.send_text(chat_id=event.chat.chat_id, text="Подписка оформлена")


@dp.command("unsubscribe")
async def cmd_unsubscribe(event, bot: Bot):
    await unsubscribe(event.chat.chat_id, "daily_reports")
    await bot.send_text(chat_id=event.chat.chat_id, text="Подписка отменена")
```

## Rate Limiting и защита от злоупотреблений

### Встроенный retry при rate limit

Бот автоматически обрабатывает HTTP 429 (rate limit) от VK Teams API с экспоненциальным backoff:

```python
from vk_teams_async_bot import Bot
from vk_teams_async_bot.client.retry import RetryPolicy

bot = Bot(
    bot_token="TOKEN",
    retry_policy=RetryPolicy(
        max_retries=5,      # максимум повторных попыток
        base_delay=1.0,     # начальная задержка (секунды)
        max_delay=30.0,     # максимальная задержка
        jitter=True,        # случайный разброс для предотвращения thundering herd
    ),
)
```

При получении `RateLimitError` бот:

1. Читает заголовок `Retry-After` (если есть) и ждёт указанное время
2. Если заголовка нет - применяет экспоненциальный backoff: `base_delay * 2^attempt` (с jitter)
3. Rate-limit retry **всегда** безопасен, т.к. сервер не выполнил запрос

### Middleware для throttling входящих событий

Ограничение частоты обработки событий от одного пользователя:

```python
import time
from collections import defaultdict

from vk_teams_async_bot import BaseMiddleware, Bot, Dispatcher

dp = Dispatcher()


class ThrottleMiddleware(BaseMiddleware):
    """Пропускает не более N событий от пользователя за period секунд."""

    def __init__(self, rate_limit: int = 5, period: float = 60.0):
        self.rate_limit = rate_limit
        self.period = period
        self.user_events: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, handler, event, data):
        user_id = getattr(event, "from_", None)
        if user_id is None:
            return await handler(event, data)

        key = str(user_id)
        now = time.monotonic()

        # Очистка устаревших записей
        self.user_events[key] = [t for t in self.user_events[key] if now - t < self.period]

        if len(self.user_events[key]) >= self.rate_limit:
            bot: Bot = data["bot"]
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"Слишком много запросов. Подождите {int(self.period)} секунд.",
            )
            return None  # не вызываем handler

        self.user_events[key].append(now)
        return await handler(event, data)


dp.add_middleware(ThrottleMiddleware(rate_limit=10, period=60.0))
```

### Распределённый rate limiting с Redis

Для ботов, запущенных в нескольких процессах/контейнерах, нужен распределённый rate limiter. `RedisStorage` обеспечивает общее состояние между инстансами:

```python
import time

from redis.asyncio import Redis

from vk_teams_async_bot import BaseMiddleware, Bot, Dispatcher


class DistributedRateLimiter:
    """Распределённый rate limiter на основе Redis sorted sets.

    Поддерживает per-user и per-group квоты. Работает корректно
    при нескольких инстансах бота, использующих один Redis.

    Алгоритм: sliding window log - каждый запрос записывается в sorted set
    с timestamp как score. Перед проверкой лимита удаляются записи старше окна.
    """

    def __init__(
        self,
        redis: Redis,
        user_limit: int = 30,
        group_limit: int = 60,
        window: int = 60,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis
        self.user_limit = user_limit
        self.group_limit = group_limit
        self.window = window
        self.key_prefix = key_prefix

    async def is_allowed(self, user_id: str, chat_id: str) -> bool:
        """Проверить, разрешён ли запрос (per-user + per-group)."""
        now = time.time()
        window_start = now - self.window

        user_key = f"{self.key_prefix}:user:{user_id}"
        group_key = f"{self.key_prefix}:group:{chat_id}"

        pipe = self.redis.pipeline()

        # Очистка старых записей + подсчёт текущих + добавление нового
        for key in (user_key, group_key):
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)

        results = await pipe.execute()
        user_count = results[1]   # zcard для user_key
        group_count = results[3]  # zcard для group_key

        if user_count >= self.user_limit or group_count >= self.group_limit:
            return False

        # Записываем событие
        pipe = self.redis.pipeline()
        pipe.zadd(user_key, {f"{now}": now})
        pipe.zadd(group_key, {f"{now}": now})
        pipe.expire(user_key, self.window + 10)
        pipe.expire(group_key, self.window + 10)
        await pipe.execute()

        return True

    async def get_remaining(self, user_id: str, chat_id: str) -> dict[str, int]:
        """Показать оставшиеся квоты."""
        now = time.time()
        window_start = now - self.window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(f"{self.key_prefix}:user:{user_id}", 0, window_start)
        pipe.zcard(f"{self.key_prefix}:user:{user_id}")
        pipe.zremrangebyscore(f"{self.key_prefix}:group:{chat_id}", 0, window_start)
        pipe.zcard(f"{self.key_prefix}:group:{chat_id}")
        results = await pipe.execute()

        return {
            "user_remaining": max(0, self.user_limit - results[1]),
            "group_remaining": max(0, self.group_limit - results[3]),
        }


class DistributedThrottleMiddleware(BaseMiddleware):
    """Middleware для распределённого rate limiting через Redis.

    Подключается к Dispatcher и автоматически ограничивает частоту
    обработки событий per-user и per-group. Корректно работает
    при запуске нескольких инстансов бота.
    """

    def __init__(self, rate_limiter: DistributedRateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, handler, event, data):
        user_id = str(getattr(event, "from_", "unknown"))
        chat_id = str(event.chat.chat_id)

        if not await self.rate_limiter.is_allowed(user_id, chat_id):
            bot: Bot = data["bot"]
            await bot.send_text(
                chat_id=chat_id,
                text="Превышен лимит запросов. Попробуйте позже.",
            )
            return None

        return await handler(event, data)


# Использование:
redis = Redis.from_url("redis://localhost:6379/0")

rate_limiter = DistributedRateLimiter(
    redis=redis,
    user_limit=30,    # 30 запросов на пользователя в минуту
    group_limit=60,   # 60 запросов на группу в минуту
    window=60,        # окно в секундах
)

dp = Dispatcher()
dp.add_middleware(DistributedThrottleMiddleware(rate_limiter))
```

### Комбинация: несколько инстансов с общим Redis

Полный пример развёртывания бота в нескольких процессах с единым rate limiting и FSM:

```python
import asyncio
import os

from redis.asyncio import Redis

from vk_teams_async_bot import Bot, Dispatcher, RedisStorage

# Общее подключение к Redis для всех компонентов
redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

# FSM-хранилище - общее для всех инстансов
storage = RedisStorage(redis=redis, key_prefix="mybot:fsm", state_ttl=3600)

# Rate limiter - общий для всех инстансов
rate_limiter = DistributedRateLimiter(
    redis=redis,
    user_limit=30,
    group_limit=100,
    window=60,
    key_prefix="mybot:ratelimit",
)

bot = Bot(bot_token=os.environ["BOT_TOKEN"], url=os.environ.get("BOT_API_URL"))
dp = Dispatcher(storage=storage)
dp.add_middleware(DistributedThrottleMiddleware(rate_limiter))


@bot.on_shutdown
async def cleanup(bot: Bot):
    await storage.close()
    await redis.aclose()


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

При запуске нескольких инстансов каждый подключается к одному Redis, что обеспечивает:

- **Единое FSM-состояние** - пользователь продолжает диалог, даже если попадает на другой инстанс
- **Общие rate-limit счётчики** - квоты per-user и per-group соблюдаются глобально
- **Sliding window** - точный подсчёт без фиксированных временных окон
- **Автоматическая очистка** - TTL на ключах предотвращает утечки памяти в Redis

## Примеры

В директории [`examples/`](examples/) находятся готовые к запуску боты:

| Пример                                                          | Что демонстрирует                               |
| --------------------------------------------------------------- | ----------------------------------------------- |
| [`echo_bot.py`](examples/echo_bot.py)                           | Минимальный echo-бот                            |
| [`start_bot.py`](examples/start_bot.py)                         | Обработка команды `/start`                      |
| [`callback_keyboard_bot.py`](examples/callback_keyboard_bot.py) | Inline-кнопки, навигация по экранам             |
| [`format_bot.py`](examples/format_bot.py)                       | MarkdownV2, HTML, Format API                    |
| [`middleware_bot.py`](examples/middleware_bot.py)               | Middleware для контроля доступа                 |
| [`send_audio.py`](examples/send_audio.py)                       | Загрузка файла, повторная отправка по `file_id` |
| [`depends.py`](examples/depends.py)                             | Dependency injection                            |
| [`showcase_bot/`](examples/showcase_bot/)                       | Полная демонстрация: все возможности вместе     |

Начните с `echo_bot.py`, затем `callback_keyboard_bot.py`, далее изучите `showcase_bot/`.

## Структура проекта

```
vk_teams_async_bot/
  bot.py            - Bot, lifecycle-хуки, polling
  dispatcher.py     - Маршрутизация событий, регистрация обработчиков
  methods/          - Реализация методов API
  types/            - Pydantic-модели (события, чаты, файлы, клавиатура, ответы)
  filters/          - Классы фильтров с композицией & | ~
  handlers/         - Классы обработчиков по типам событий
  fsm/              - State, StatesGroup, FSMContext, хранилище
  middleware/        - BaseMiddleware, MiddlewareManager, SessionTimeout
  client/           - HTTP-сессия, retry policy
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

Подробное руководство по обновлению с примерами "до/после" - см. [MIGRATION.md](MIGRATION.md).

Ключевые изменения в 1.0.0:

- Все импорты из верхнеуровневого `vk_teams_async_bot`
- `Bot` - контекстный менеджер; `start_polling()` принимает `Dispatcher`
- Типизированные Pydantic-события вместо dict-обёрток
- Новая система фильтров с операторами композиции
- `FSMContext` + `MemoryStorage` вместо `DictUserState`
- `BaseMiddleware` с протоколом `__call__(handler, event, data)`

## Важные замечания

- Только long polling (webhook не поддерживается).
- `Dispatcher` вызывает только **первый** подходящий обработчик для каждого события.
- События обрабатываются параллельно (лимит: `max_concurrent_handlers`). События с одинаковым `(chat_id, user_id)` сериализуются автоматически при подключённом FSM-хранилище.
- `MemoryStorage` хранит состояние в памяти процесса (подходит для простых ботов). Для масштабируемых решений - `RedisStorage` (`pip install vk-teams-async-bot[redis]`).
- `create_chat()` и `add_chat_members()` требуют on-premise VK Teams с настройкой администратора.

## Лицензия

[MIT](LICENSE) - Смирнов Александр (Quakeer444)
