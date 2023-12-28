import asyncio

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.constants import ParseMode
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.handler import MessageHandler

app = Bot(bot_token="TOKEN", url="URL")


async def echo_handler(event: Event, bot: Bot):
    without_format = "hello"
    markdownv2 = "*hello*"
    html = "<b>html</b>"

    await bot.send_text(chat_id=event.chat.chatId, text=without_format)

    await bot.send_text(
        chat_id=event.chat.chatId, text=markdownv2, parse_mode=ParseMode.MARKDOWNV2
    )
    await bot.send_text(chat_id=event.chat.chatId, text=html, parse_mode=ParseMode.HTML)


app.dispatcher.add_handler(
    MessageHandler(
        callback=echo_handler,
    )
)


async def main():
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
