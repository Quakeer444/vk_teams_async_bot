from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    CommandFilter,
    Dispatcher,
    FileFilter,
    ForwardFilter,
    FSMContext,
    MentionFilter,
    NewMessageEvent,
    RegexpFilter,
    ReplyFilter,
    StateFilter,
    StickerFilter,
    TagFilter,
    VoiceFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import back_to_main_kb, filter_parts_kb, filters_menu_kb
from ..states import FilterDemoStates


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


def register_filters_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:flt"))
    async def show_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Фильтры сообщений\n\nВыберите, какие фильтры хотите посмотреть:",
            filters_menu_kb(),
        )

    # -- Part Filters --
    @dp.callback_query(CallbackDataFilter("flt:parts"))
    async def show_part_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Фильтры по типу вложения\n\nВыберите фильтр для теста. После этого отправьте подходящий контент.",
            filter_parts_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:file"))
    async def test_file_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_file)
        await safe_edit(event, bot, "Тест FileFilter\n\nОтправьте мне любой файл.", back_to_main_kb())

    @dp.callback_query(CallbackDataFilter("flt:part:voice"))
    async def test_voice_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_voice)
        await safe_edit(event, bot, "Тест VoiceFilter\n\nОтправьте мне голосовое сообщение.", back_to_main_kb())

    @dp.callback_query(CallbackDataFilter("flt:part:sticker"))
    async def test_sticker_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await bot.answer_callback_query(query_id=event.query_id)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="Тест StickerFilter\n\nОтправьте мне стикер. (StickerFilter всегда активен глобально.)",
            inline_keyboard_markup=back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:mention"))
    async def test_mention_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_mention)
        await safe_edit(event, bot, "Тест MentionFilter\n\nОтправьте сообщение с упоминанием кого-либо.", back_to_main_kb())

    @dp.callback_query(CallbackDataFilter("flt:part:reply"))
    async def test_reply_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_reply)
        await safe_edit(event, bot, "Тест ReplyFilter\n\nОтветьте на любое сообщение.", back_to_main_kb())

    @dp.callback_query(CallbackDataFilter("flt:part:forward"))
    async def test_forward_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_forward)
        await safe_edit(event, bot, "Тест ForwardFilter\n\nПерешлите сюда любое сообщение.", back_to_main_kb())

    # State-guarded part filter handlers
    @dp.message(StateFilter(FilterDemoStates.waiting_for_file, storage), FileFilter())
    async def got_file(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="FileFilter сработал! Файл обнаружен.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_voice, storage), VoiceFilter())
    async def got_voice(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="VoiceFilter сработал! Голосовое сообщение обнаружено.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_mention, storage), MentionFilter())
    async def got_mention(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="MentionFilter сработал! Упоминание обнаружено.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_reply, storage), ReplyFilter())
    async def got_reply(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="ReplyFilter сработал! Ответ обнаружен.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_forward, storage), ForwardFilter())
    async def got_forward(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="ForwardFilter сработал! Пересылка обнаружена.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    # -- Text Filters --
    @dp.callback_query(CallbackDataFilter("flt:text"))
    async def show_text_filters(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Текстовые фильтры\n\n"
            "Эти фильтры зарегистрированы глобально:\n"
            "- RegexpFilter: отправьте email для теста\n"
            "- TagFilter: отправьте 'hello', 'hi' или 'hey'\n"
            "- CommandFilter: отправьте /demo"
        )
        await safe_edit(event, bot, text, back_to_main_kb())

    @dp.message(RegexpFilter(r"^[\w.+-]+@[\w-]+\.[\w.]+$"))
    async def regexp_match(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"RegexpFilter сработал! Обнаружен email: {event.text}",
        )

    @dp.message(TagFilter(["hello", "hi", "hey"]))
    async def tag_match(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"TagFilter сработал! Вы сказали: {event.text}",
        )

    @dp.message(CommandFilter("demo"))
    async def command_match(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="CommandFilter сработал! Команда /demo получена.",
        )

    # -- Composite Filters --
    @dp.callback_query(CallbackDataFilter("flt:composite"))
    async def show_composite(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Составные фильтры\n\n"
            "Фильтры можно комбинировать:\n"
            "- AND (&): ответ с прикрепленным файлом\n"
            "- OR (|): файл или голосовое сообщение\n"
            "- NOT (~): любое сообщение, которое НЕ стикер\n\n"
            "Это демонстрируется существующими фильтрами."
        )
        await safe_edit(event, bot, text, back_to_main_kb())

    # -- Advanced Filters --
    @dp.callback_query(CallbackDataFilter("flt:advanced"))
    async def show_advanced(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Продвинутые фильтры\n\n"
            "- RegexpTextPartsFilter: регулярные выражения по тексту в пересланных/ответных частях\n"
            "- MessageTextPartFromNickFilter: фильтр частей по нику отправителя\n"
            "- CallbackDataRegexpFilter: регулярные выражения по callback data\n\n"
            "Используются внутри этого бота для маршрутизации."
        )
        await safe_edit(event, bot, text, back_to_main_kb())
