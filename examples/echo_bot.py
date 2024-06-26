import asyncio

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.handler import MessageHandler
from local_.config import env

app = Bot(bot_token=env.TEST_BOT_TOKEN.get_secret_value())


async def echo_handler(event: Event, bot: Bot):
    await bot.send_text(chat_id=event.chat.chatId, text=event.text)


app.dispatcher.add_handler(
    MessageHandler(
        callback=echo_handler,
    )
)


async def main():
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
