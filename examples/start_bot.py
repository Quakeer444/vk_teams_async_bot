import asyncio
import os

from vk_teams_async_bot import Bot, CommandFilter, Dispatcher, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


@dp.message(CommandFilter("start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Hello")


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
