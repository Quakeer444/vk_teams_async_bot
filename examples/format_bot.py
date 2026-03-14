import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent, ParseMode

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


@dp.message()
async def format_handler(event: NewMessageEvent, bot: Bot):
    without_format = "hello"
    markdownv2 = "*hello*"
    html = "<b>html</b>"

    await bot.send_text(chat_id=event.chat.chat_id, text=without_format)
    await bot.send_text(
        chat_id=event.chat.chat_id, text=markdownv2, parse_mode=ParseMode.MARKDOWNV2
    )
    await bot.send_text(
        chat_id=event.chat.chat_id, text=html, parse_mode=ParseMode.HTML
    )


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
