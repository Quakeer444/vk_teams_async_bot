[![PyPi Package Version](https://img.shields.io/pypi/v/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![Package dwn stats](https://img.shields.io/pypi/dm/vk-teams-async-bot)](https://pypi.org/project/vk-teams-async-bot/)
[![Repo size](https://img.shields.io/github/repo-size/Quakeer444/vk_teams_async_bot)](https://pypi.org/project/vk-teams-async-bot/)


# vk-teams-async-bot

Async Python library for building VK Teams bots via VK Teams Bot API.

API docs: https://teams.vk.com/botapi/

[Metabot](https://teams.vk.com/profile/70001) -- for creating a bot and getting a token.

## Table of Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Implemented Methods](#implemented-methods)
- [Examples](#examples)
  - [Send Messages with Formatting](#send-messages-with-formatting)
  - [Inline Keyboard](#inline-keyboard)
  - [Middleware](#middleware)
- [Migration from 0.2.x](#migration-from-02x)

## Installation

```bash
pip install -U vk-teams-async-bot
# OR
poetry add vk-teams-async-bot
```

## Quickstart

Set `BOT_TOKEN` environment variable (or pass directly):

```python
import asyncio
import os

from vk_teams_async_bot import Bot, CommandFilter, Dispatcher, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


@dp.message(CommandFilter("/start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Hello!")


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
```

## Implemented Methods

| # | Endpoint | Method | HTTP |
|---|----------|--------|------|
| 1 | /self/get | `get_self()` | GET |
| 2 | /messages/sendText | `send_text(chat_id, text, ...)` | GET |
| 3 | /messages/sendFile | `send_file(chat_id, file_id=... or file=...)` | GET/POST |
| 4 | /messages/sendVoice | `send_voice(chat_id, file_id=... or file=...)` | GET/POST |
| 5 | /messages/editText | `edit_text(chat_id, msg_id, text, ...)` | GET |
| 6 | /messages/deleteMessages | `delete_messages(chat_id, msg_id)` | GET |
| 7 | /messages/answerCallbackQuery | `answer_callback_query(query_id, ...)` | GET |
| 8 | /chats/createChat | `create_chat(name, ...)` | GET |
| 9 | /chats/avatar/set | `set_chat_avatar(chat_id, image)` | POST |
| 10 | /chats/members/add | `add_chat_members(chat_id, members)` | GET |
| 11 | /chats/members/delete | `delete_chat_members(chat_id, members)` | GET |
| 12 | /chats/sendActions | `send_chat_actions(chat_id, actions)` | GET |
| 13 | /chats/getInfo | `get_chat_info(chat_id)` | GET |
| 14 | /chats/getAdmins | `get_chat_admins(chat_id)` | GET |
| 15 | /chats/getMembers | `get_chat_members(chat_id, cursor=...)` | GET |
| 16 | /chats/getBlockedUsers | `get_blocked_users(chat_id)` | GET |
| 17 | /chats/getPendingUsers | `get_pending_users(chat_id)` | GET |
| 18 | /chats/blockUser | `block_user(chat_id, user_id, ...)` | GET |
| 19 | /chats/unblockUser | `unblock_user(chat_id, user_id)` | GET |
| 20 | /chats/resolvePending | `resolve_pending(chat_id, approve, ...)` | GET |
| 21 | /chats/setTitle | `set_chat_title(chat_id, title)` | GET |
| 22 | /chats/setAbout | `set_chat_about(chat_id, about)` | GET |
| 23 | /chats/setRules | `set_chat_rules(chat_id, rules)` | GET |
| 24 | /chats/pinMessage | `pin_message(chat_id, msg_id)` | GET |
| 25 | /chats/unpinMessage | `unpin_message(chat_id, msg_id)` | GET |
| 26 | /files/getInfo | `get_file_info(file_id)` | GET |
| 27 | /events/get | `get_events(last_event_id, poll_time)` | GET |

## Examples

### Send Messages with Formatting

```python
from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent, ParseMode

dp = Dispatcher()

@dp.message()
async def format_handler(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="plain text")
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="*bold* _italic_ __underline__",
        parse_mode=ParseMode.MARKDOWNV2,
    )
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="<b>bold</b>",
        parse_mode=ParseMode.HTML,
    )
```

#### MarkdownV2 Syntax

```
*bold*           _italic_          __underline__
~strikethrough~  `inline code`     ```code block```
[link](url)      @\[user@corp\]    >quote
```

### Inline Keyboard

```python
from vk_teams_async_bot import (
    Bot, CallbackDataFilter, CallbackQueryEvent, CommandFilter,
    Dispatcher, InlineKeyboardMarkup, KeyboardButton,
    NewMessageEvent, StyleKeyboard,
)

dp = Dispatcher()

def start_keyboard():
    kb = InlineKeyboardMarkup(buttons_in_row=3)
    kb.add(
        KeyboardButton(text="Button 1", callback_data="cb_one", style=StyleKeyboard.PRIMARY),
        KeyboardButton(text="Button 2", callback_data="cb_two", style=StyleKeyboard.BASE),
        KeyboardButton(text="Link", url="https://example.com/", style=StyleKeyboard.ATTENTION),
    )
    return kb

@dp.message(CommandFilter("/start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(
        chat_id=event.chat.chat_id,
        text="Choose an option:",
        inline_keyboard_markup=start_keyboard(),
    )

@dp.callback_query(CallbackDataFilter("cb_one"))
async def on_button(event: CallbackQueryEvent, bot: Bot):
    await bot.answer_callback_query(query_id=event.query_id, text="Clicked!")
```

### Middleware

```python
from vk_teams_async_bot import BaseMiddleware, Dispatcher

dp = Dispatcher()

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print(f"Event: {event.type}")
        result = await handler(event, data)
        print(f"Done: {event.type}")
        return result

dp.add_middleware(LoggingMiddleware())
```

## Migration from 0.2.x

See [MIGRATION.md](MIGRATION.md) for a complete migration guide with before/after examples.
