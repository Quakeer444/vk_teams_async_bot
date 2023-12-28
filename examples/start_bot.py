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
