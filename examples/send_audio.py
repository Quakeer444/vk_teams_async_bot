import asyncio
import os

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


@dp.message()
async def file_handler(event: NewMessageEvent, bot: Bot):
    path_image = "../images/img_3.png"
    path_pdf = "../images/png2pdf.pdf"
    path_audio = "../images/test.mp3"

    result_image = await bot.send_file(
        chat_id=event.chat.chat_id,
        file=path_image,
        caption="this is the test image",
    )
    result_pdf = await bot.send_file(
        chat_id=event.chat.chat_id,
        file=path_pdf,
        caption="this is the test pdf file",
    )
    result_audio = await bot.send_voice(
        chat_id=event.chat.chat_id,
        file=path_audio,
    )

    await bot.send_file(
        chat_id=event.chat.chat_id,
        file_id=result_image.file_id,
        caption="Image from the Bot API server",
    )
    await bot.send_file(
        chat_id=event.chat.chat_id,
        file_id=result_pdf.file_id,
        caption="Pdf from the Bot API server",
    )
    await bot.send_voice(
        chat_id=event.chat.chat_id,
        file_id=result_audio.file_id,
    )


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
