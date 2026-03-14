import io
import struct
import wave

from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    ChatAction,
    Dispatcher,
    FileFilter,
    FSMContext,
    NewMessageEvent,
    StateFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import back_to_main_kb, files_menu_kb
from ..states import FileReceiveStates


def _make_tiny_png() -> io.BytesIO:
    """Generate a minimal 1x1 red PNG in memory."""
    # Minimal valid PNG: 1x1 red pixel
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw_row = b"\x00\xff\x00\x00"  # filter=none, R=255, G=0, B=0
    compressed = zlib.compress(raw_row)
    png = signature + _chunk(b"IHDR", ihdr_data) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")
    buf = io.BytesIO(png)
    buf.name = "test.png"
    return buf


def _make_tiny_wav() -> io.BytesIO:
    """Generate a minimal WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        # 0.1 second of silence
        w.writeframes(b"\x00\x00" * 800)
    buf.seek(0)
    buf.name = "test.wav"
    return buf


async def safe_edit(event: CallbackQueryEvent, bot: Bot, text: str, keyboard=None):
    await bot.answer_callback_query(query_id=event.query_id)
    if event.message:
        await bot.edit_text(
            chat_id=event.chat.chat_id,
            msg_id=event.message.msg_id,
            text=text,
            inline_keyboard_markup=keyboard,
        )
    else:
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=keyboard,
        )


def register_files_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:file"))
    async def show_files(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Демо файлов\n\nВыберите действие:",
            files_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("file:send:img"))
    async def send_image(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id, text="Отправка изображения...")
        chat_id = event.chat.chat_id
        await bot.send_chat_actions(chat_id, actions=[ChatAction.TYPING])
        png_buf = _make_tiny_png()
        await bot.send_file(
            chat_id,
            file=("test.png", png_buf, "image/png"),
            caption="Тестовый красный пиксель 1x1",
        )

    @dp.callback_query(CallbackDataFilter("file:send:voice"))
    async def send_voice(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id, text="Отправка голосового...")
        chat_id = event.chat.chat_id
        await bot.send_chat_actions(chat_id, actions=[ChatAction.TYPING])
        wav_buf = _make_tiny_wav()
        await bot.send_voice(
            chat_id,
            file=("test.wav", wav_buf, "audio/wav"),
        )

    @dp.callback_query(CallbackDataFilter("file:info"))
    async def bot_info(event: CallbackQueryEvent, bot: Bot):
        await bot.answer_callback_query(query_id=event.query_id)
        info = await bot.get_self()
        lines = [
            "Информация о боте",
            "",
            f"User ID: {info.user_id}",
            f"Ник: {info.nick or '(нет)'}",
            f"Имя: {info.first_name or '(нет)'}",
            f"О боте: {info.about or '(нет)'}",
        ]
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="\n".join(lines),
            inline_keyboard_markup=files_menu_kb(),
        )

    @dp.callback_query(CallbackDataFilter("file:receive"))
    async def start_receive(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FileReceiveStates.waiting_for_file)
        await safe_edit(
            event, bot,
            "Отправьте мне любой файл и я:\n1. Получу информацию о файле\n2. Скачаю его\n3. Отправлю обратно по file_id",
            back_to_main_kb(),
        )

    @dp.message(StateFilter(FileReceiveStates.waiting_for_file, storage), FileFilter())
    async def receive_file(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        chat_id = event.chat.chat_id

        if not event.parts:
            await bot.send_text(chat_id, "Части файла не найдены.", inline_keyboard_markup=files_menu_kb())
            return

        file_part = event.parts[0]
        file_id = file_part.payload.file_id

        # 1. Get file info
        file_info = await bot.get_file_info(file_id)
        info_text = (
            f"Информация о файле:\n"
            f"  Тип: {file_info.type}\n"
            f"  Размер: {file_info.size} байт\n"
            f"  Имя файла: {file_info.filename}\n"
            f"  URL: {file_info.url}\n"
        )
        await bot.send_text(chat_id, info_text)

        # 2. Download file
        file_bytes = await bot.download_file(file_info.url)
        await bot.send_text(chat_id, f"Скачано {len(file_bytes)} байт")

        # 3. Resend by file_id
        await bot.send_file(
            chat_id,
            file_id=file_id,
            caption="Отправлено повторно по file_id",
            inline_keyboard_markup=files_menu_kb(),
        )
