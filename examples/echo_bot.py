import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, MessageHandler, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


@dp.message()
async def echo_handler(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text=event.text or "")


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
