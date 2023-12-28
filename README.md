# **Table of Contents**

- [Examples](#examples)
  - [Basic initialization](#basic-initialization)
  - [Send messages](#send-messages)
    - [Without formatting](#without-formatting)
    - [MarkdownV2](#markdownv2) 
  - [InlineKeyboard](#inlinekeyboard)



# Examples

## Basic initialization
```python
import asyncio

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.filter import Filter
from vk_teams_async_bot.handler import CommandHandler

app = Bot(bot_token="TOKEN", url="URL")


async def cmd_start(event: Event, bot: Bot):
    await bot.send_text(chat_id=event.chat.chatId, text="Hello")


app.dispatcher.add_handler(
    CommandHandler(callback=cmd_start, filters=Filter.command("/start")),
)


async def main():
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())

```

## Send messages

### Without formatting

```python
async def cmd_start(event: Event, bot: Bot):
    await bot.send_text(chat_id=event.chat.chatId, text="Hello")
    await bot.send_text(chat_id=event.chat.chatId, text="<b>Hello</b>")
    await bot.send_text(chat_id=event.chat.chatId, text="*Hello*")
```
Result:

![image](images/img.png)


### MarkdownV2

`parse_mode=ParseMode.MARKDOWNV2`

- All special characters that do not represent the beginning or end of the style must be escaped using a backslash \
#### Methods MarkdownV2
```plain text
1. *hello*   -  bold
2. _hello_   -  italic
3. __hello__ -  underline
4. ~hello~   -  strikethrought
5. [hello](https://example.com) - hyperlinked text
6. @\[user@company\]            - to mention the VK Teams user
7. ```hello```                  - inline code
8. ```python print("hello") ``` - multiline block code
9.  Ordered list:
    1. First element
    2. Second element
10. Unordered list:
    - First element
    - Second element
11. Quote:
    >Begin of quote
    >End of quote
```

```python
async def cmd_start(event: Event, bot: Bot):
    text = \
        """
        *hello*
        _hello_
        __hello__
        """

    await bot.send_text(
        chat_id=event.chat.chatId, text=text, parse_mode=ParseMode.MARKDOWNV2
    )
```
Result:

![image](images/img_1.png)


## InlineKeyboard

```python
from vk_teams_async_bot.constants import StyleKeyboard
from vk_teams_async_bot.handler import CommandHandler
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton

def keyboad_start_menu():
    keyboard = InlineKeyboardMarkup(buttons_in_row=3)
    keyboard.add(
        KeyboardButton(
            text="🛠 first button",
            callback_data="cb_one",
            style=StyleKeyboard.PRIMARY,
        ),
        KeyboardButton(
            text="🕹 second button",
            callback_data="cb_two",
            style=StyleKeyboard.BASE,
        ),
        KeyboardButton(
            text="🌐 third button",
            url="https://example.com/",
            style=StyleKeyboard.ATTENTION,
        ),
    )
    return keyboard


async def cmd_start(event: Event, bot: Bot):
    text = """hello"""
    await bot.send_text(
        chat_id=event.chat.chatId,
        text=text,
        inline_keyboard_markup=keyboad_start_menu(),
    )
```


![image](images/img_2.png)

You can specify the number of buttons in a row
`InlineKeyboardMarkup(buttons_in_row=1)`

![image](images/img_3.png)



