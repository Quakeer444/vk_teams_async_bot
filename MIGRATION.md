# Migration Guide: 0.2.x -> 1.0.0

## Imports

All public classes are now available from the top-level package:

```python
# Before (0.2.x)
from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.filter import Filter
from vk_teams_async_bot.handler import CommandHandler, MessageHandler, BotButtonCommandHandler
from vk_teams_async_bot.constants import ParseMode, StyleKeyboard
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton
from vk_teams_async_bot.middleware import Middleware
from vk_teams_async_bot.state import DictUserState

# After (1.0.0)
from vk_teams_async_bot import (
    Bot, Dispatcher,
    NewMessageEvent, CallbackQueryEvent, EditedMessageEvent,
    CommandHandler, MessageHandler, CallbackQueryHandler,
    CommandFilter, CallbackDataFilter, MessageFilter,
    ParseMode, StyleKeyboard,
    InlineKeyboardMarkup, KeyboardButton,
    BaseMiddleware,
    FSMContext, MemoryStorage, State, StatesGroup,
)
```

## Bot Initialization & Lifecycle

The `Bot` is now a context manager. `start_polling()` requires a `Dispatcher`:

```python
# Before (0.2.x)
app = Bot(bot_token="TOKEN")
app.dispatcher.add_handler(...)
asyncio.run(app.start_polling())

# After (1.0.0)
bot = Bot(bot_token="TOKEN")
dp = Dispatcher()

@dp.message(CommandFilter("/start"))
async def on_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(event.chat.chat_id, "Hello!")

async def main():
    async with bot:
        await bot.start_polling(dp)

asyncio.run(main())
```

## Event Access

Events are now typed Pydantic models instead of dict wrappers:

```python
# Before (0.2.x)
async def handler(event: Event, bot: Bot):
    chat_id = event.chat.chatId
    text = event.text
    query_id = event.queryId
    msg_id = event.cb_message.msgId

# After (1.0.0)
async def message_handler(event: NewMessageEvent, bot: Bot):
    chat_id = event.chat.chat_id    # snake_case
    text = event.text

async def callback_handler(event: CallbackQueryEvent, bot: Bot):
    query_id = event.query_id       # snake_case
    msg_id = event.message.msg_id   # .message instead of .cb_message
```

## Handler Registration

Use decorator shortcuts or the new handler classes:

```python
# Before (0.2.x)
app.dispatcher.add_handler(
    CommandHandler(callback=cmd_start, filters=Filter.command("/start"))
)
app.dispatcher.add_handler(
    BotButtonCommandHandler(callback=on_button, filters=Filter.callback_data("cb_ok"))
)

# After (1.0.0) -- decorator style
@dp.message(CommandFilter("/start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    ...

@dp.callback_query(CallbackDataFilter("cb_ok"))
async def on_button(event: CallbackQueryEvent, bot: Bot):
    ...

# After (1.0.0) -- imperative style (also works)
dp.add_handler(CommandHandler(callback=cmd_start, filters=CommandFilter("/start")))
dp.add_handler(CallbackQueryHandler(callback=on_button, filters=CallbackDataFilter("cb_ok")))
```

## Filters

Filters are now standalone classes instead of `Filter.xxx()` static methods:

```python
# Before (0.2.x)
Filter.command("/start")
Filter.callback_data("cb_ok")

# After (1.0.0)
CommandFilter("/start")
CallbackDataFilter("cb_ok")
RegexpFilter(r"hello.*")
MessageFilter()  # matches any message

# Filter composition
CommandFilter("/start") & MessageFilter()   # AND
CommandFilter("/help") | CommandFilter("/start")  # OR
~FileFilter()  # NOT (messages without files)
```

## Middleware

The middleware protocol has changed:

```python
# Before (0.2.x)
class AccessMiddleware(Middleware):
    async def handle(self, event, bot):
        if event.chat.chatId not in allowed:
            raise PermissionError()
        return event

app.dispatcher.middlewares = [AccessMiddleware()]

# After (1.0.0)
class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        bot = data["bot"]
        if hasattr(event, "chat") and event.chat.chat_id not in allowed:
            return  # short-circuit, don't call handler
        return await handler(event, data)

dp.add_middleware(AccessMiddleware())
```

## FSM (State Management)

`DictUserState` is replaced by `MemoryStorage` + `FSMContext`:

```python
# Before (0.2.x)
from vk_teams_async_bot.state import DictUserState

state = DictUserState()
state.set_state(user_id, "waiting_name")
current = state.get_state(user_id)

# After (1.0.0)
from vk_teams_async_bot import (
    Dispatcher, MemoryStorage, State, StatesGroup, FSMContext,
)

class Form(StatesGroup):
    waiting_name = State()
    waiting_age = State()

dp = Dispatcher(storage=MemoryStorage())

@dp.message(StateFilter(Form.waiting_name))
async def process_name(event: NewMessageEvent, bot: Bot):
    fsm = bot._fsm_context
    await fsm.set_state(Form.waiting_age)
    await fsm.update_data(name=event.text)
```

Key difference: FSM now keys on `(chat_id, user_id)` instead of just `user_id`, so the same user can have different states in different chats.

## Method Return Types

All bot methods now return Pydantic models:

```python
# Before (0.2.x)
result = await bot.send_file(chat_id=..., file_path=path)
file_id = result["fileId"]  # raw dict access

# After (1.0.0)
result = await bot.send_file(chat_id=..., file=path)
file_id = result.file_id  # typed attribute access
```

## Method Signature Changes

Some method signatures have changed:

```python
# send_file: file_path -> file (path or tuple), or file_id for by-id
await bot.send_file(chat_id=..., file="path/to/file.png")
await bot.send_file(chat_id=..., file_id="existing_file_id")

# send_voice: same pattern
await bot.send_voice(chat_id=..., file="path/to/audio.mp3")
await bot.send_voice(chat_id=..., file_id="existing_file_id")

# delete_messages (was delete_msg)
await bot.delete_messages(chat_id=..., msg_id=msg_id)
```
