import asyncio

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.handler import MessageHandler

app = Bot(bot_token="TOKEN", url="URL")


async def echo_handler(event: Event, bot: Bot):
    path_image = r"..\images\img_3.png"
    path_pdf = r"..\images\png2pdf.pdf"
    path_audio = r"..\images\test.mp3"

    result_image = await bot.send_file(
        chat_id=event.chat.chatId,
        file_path=path_image,
        filename="test_image/png",
        caption="this is the test image",
    )
    result_pdf = await bot.send_file(
        chat_id=event.chat.chatId,
        file_path=path_pdf,
        filename="test_pdf.pdf",
        caption="this is the test pdf file",
    )
    result_audio = await bot.send_voice(
        chat_id=event.chat.chatId,
        file_path=path_audio,
        filename="test_audio.mp3",
    )

    image_id = result_image["fileId"]
    pdf_id = result_pdf["fileId"]
    audio_id = result_audio["fileId"]

    await bot.send_file_by_id(
        chat_id=event.chat.chatId,
        file_id=image_id,
        caption="Image from the Bot API server",
    )
    await bot.send_file_by_id(
        chat_id=event.chat.chatId, file_id=pdf_id, caption="Pdf from the Bot API server"
    )
    await bot.send_voice_by_id(chat_id=event.chat.chatId, file_id=audio_id)


app.dispatcher.add_handler(
    MessageHandler(
        callback=echo_handler,
    )
)


async def main():
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
