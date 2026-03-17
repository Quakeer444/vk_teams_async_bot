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
    MessageTextPartFromNickFilter,
    NewMessageEvent,
    RegexpFilter,
    RegexpTextPartsFilter,
    ReplyFilter,
    StateFilter,
    StickerFilter,
    TagFilter,
    VoiceFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import (
    back_to_main_kb,
    filter_advanced_kb,
    filter_composite_kb,
    filter_parts_kb,
    filters_menu_kb,
)
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
        await fsm_context.set_state(FilterDemoStates.waiting_for_sticker)
        await safe_edit(event, bot, "Тест StickerFilter\n\nОтправьте мне стикер.", back_to_main_kb())

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

    @dp.message(StateFilter(FilterDemoStates.waiting_for_sticker, storage), StickerFilter())
    async def got_sticker(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="StickerFilter сработал! Стикер обнаружен.",
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
            "Фильтры можно комбинировать операторами &, |, ~.\n"
            "Выберите комбинацию для теста:"
        )
        await safe_edit(event, bot, text, filter_composite_kb())

    @dp.callback_query(CallbackDataFilter("flt:comp:and"))
    async def test_and_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_and)
        await safe_edit(
            event, bot,
            "Тест AND: ReplyFilter() & FileFilter()\n\n"
            "Ответьте на любое сообщение и прикрепите файл к ответу.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:comp:or"))
    async def test_or_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_or)
        await safe_edit(
            event, bot,
            "Тест OR: FileFilter() | VoiceFilter()\n\n"
            "Отправьте файл или голосовое сообщение.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:comp:not"))
    async def test_not_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_not)
        await safe_edit(
            event, bot,
            "Тест NOT: ~StickerFilter()\n\n"
            "Отправьте любое сообщение, которое НЕ является стикером.",
            back_to_main_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_and, storage), ReplyFilter() & FileFilter())
    async def got_and(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="AND-фильтр сработал! Ответ с файлом обнаружен.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_or, storage), FileFilter() | VoiceFilter())
    async def got_or(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="OR-фильтр сработал! Файл или голосовое обнаружено.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_not, storage), ~StickerFilter())
    async def got_not(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="NOT-фильтр сработал! Сообщение не является стикером.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    # -- Advanced Filters --
    @dp.callback_query(CallbackDataFilter("flt:advanced"))
    async def show_advanced(event: CallbackQueryEvent, bot: Bot):
        text = (
            "Продвинутые фильтры\n\n"
            "Фильтры для работы с вложенными частями сообщений.\n"
            "Выберите фильтр для теста:"
        )
        await safe_edit(event, bot, text, filter_advanced_kb())

    @dp.callback_query(CallbackDataFilter("flt:adv:regexp"))
    async def test_regexp_parts(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(FilterDemoStates.waiting_for_regexp_parts)
        await safe_edit(
            event, bot,
            "Тест RegexpTextPartsFilter(r\"https?://\\S+\")\n\n"
            "Перешлите или ответьте на сообщение, содержащее URL.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:adv:nick"))
    async def test_nick_parts(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        bot_info = await bot.get_self()
        nick = bot_info.nick or "unknown"
        await fsm_context.set_state(FilterDemoStates.waiting_for_nick_parts)
        await fsm_context.update_data(bot_nick=nick)
        await safe_edit(
            event, bot,
            f"Тест MessageTextPartFromNickFilter(\"{nick}\")\n\n"
            f"Перешлите или ответьте на сообщение от этого бота (@{nick}).",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:adv:cbregexp"))
    async def show_cbregexp_info(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "CallbackDataRegexpFilter\n\n"
            "Этот фильтр уже используется во всем боте для маршрутизации "
            "callback-запросов. Все кнопки с префиксами btn:, nav:, fmt:, wzb: и т.д. "
            "обрабатываются именно через CallbackDataRegexpFilter(r\"^prefix:\").",
            filter_advanced_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_regexp_parts, storage), RegexpTextPartsFilter(r"https?://\S+"))
    async def got_regexp_parts(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="RegexpTextPartsFilter сработал! URL найден в пересланном/ответном сообщении.",
            inline_keyboard_markup=filter_advanced_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_nick_parts, storage))
    async def got_nick_parts(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        data = await fsm_context.get_data()
        nick = data.get("bot_nick", "")
        flt = MessageTextPartFromNickFilter(nick)
        if flt(event):
            await fsm_context.clear()
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"MessageTextPartFromNickFilter сработал! Обнаружена часть от @{nick}.",
                inline_keyboard_markup=filter_advanced_kb(),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"Не подходит. Перешлите или ответьте на сообщение от @{nick}.",
            )
