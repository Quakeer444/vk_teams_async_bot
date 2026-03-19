from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    ChatIdFilter,
    ChatTypeFilter,
    CommandFilter,
    Dispatcher,
    FileFilter,
    FileTypeFilter,
    ForwardFilter,
    FromUserFilter,
    FSMContext,
    MentionFilter,
    MentionUserFilter,
    MessageTextPartFromNickFilter,
    NewMessageEvent,
    RegexpFilter,
    RegexpTextPartsFilter,
    ReplyFilter,
    StateFilter,
    StickerFilter,
    TagFilter,
    TextFilter,
    VoiceFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards import (
    back_to_main_kb,
    filter_advanced_kb,
    filter_composite_kb,
    filter_parts_kb,
    filter_text_user_kb,
    filters_menu_kb,
)
from ..states import FilterDemoStates
from .utils import safe_edit


def register_filters_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:flt"))
    async def show_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Фильтры сообщений\n\nВыберите, какие фильтры хотите посмотреть:",
            filters_menu_kb(),
        )

    # -- Part Filters --
    @dp.callback_query(CallbackDataFilter("flt:parts"))
    async def show_part_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Фильтры по типу вложения\n\nВыберите фильтр для теста. После этого отправьте подходящий контент.",
            filter_parts_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:file"))
    async def test_file_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_file)
        await safe_edit(
            event,
            bot,
            "Тест FileFilter\n\nОтправьте мне любой файл.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:voice"))
    async def test_voice_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_voice)
        await safe_edit(
            event,
            bot,
            "Тест VoiceFilter\n\nОтправьте мне голосовое сообщение.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:sticker"))
    async def test_sticker_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_sticker)
        await safe_edit(
            event, bot, "Тест StickerFilter\n\nОтправьте мне стикер.", back_to_main_kb()
        )

    @dp.callback_query(CallbackDataFilter("flt:part:mention"))
    async def test_mention_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_mention)
        await safe_edit(
            event,
            bot,
            "Тест MentionFilter\n\nОтправьте сообщение с упоминанием кого-либо.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:reply"))
    async def test_reply_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_reply)
        await safe_edit(
            event,
            bot,
            "Тест ReplyFilter\n\nОтветьте на любое сообщение.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:part:forward"))
    async def test_forward_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_forward)
        await safe_edit(
            event,
            bot,
            "Тест ForwardFilter\n\nПерешлите сюда любое сообщение.",
            back_to_main_kb(),
        )

    # State-guarded part filter handlers (specific handler THEN fallback for each state)
    @dp.message(StateFilter(FilterDemoStates.waiting_for_file, storage), FileFilter())
    async def got_file(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="FileFilter сработал! Файл обнаружен.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_file, storage))
    async def fallback_file(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается файл. Отправьте файл или /cancel."
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_voice, storage), VoiceFilter())
    async def got_voice(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="VoiceFilter сработал! Голосовое сообщение обнаружено.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_voice, storage))
    async def fallback_voice(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается голосовое сообщение. Или /cancel."
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_mention, storage), MentionFilter()
    )
    async def got_mention(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="MentionFilter сработал! Упоминание обнаружено.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_mention, storage))
    async def fallback_mention(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается упоминание (@user). Или /cancel."
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_reply, storage), ReplyFilter())
    async def got_reply(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="ReplyFilter сработал! Ответ обнаружен.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_reply, storage))
    async def fallback_reply(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается ответ на сообщение. Или /cancel."
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_forward, storage), ForwardFilter()
    )
    async def got_forward(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="ForwardFilter сработал! Пересылка обнаружена.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_forward, storage))
    async def fallback_forward(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается пересланное сообщение. Или /cancel."
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_sticker, storage), StickerFilter()
    )
    async def got_sticker(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="StickerFilter сработал! Стикер обнаружен.",
            inline_keyboard_markup=filter_parts_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_sticker, storage))
    async def fallback_sticker(event: NewMessageEvent, bot: Bot):
        await bot.send_text(event.chat.chat_id, "Ожидается стикер. Или /cancel.")

    # -- Text Filters --
    @dp.callback_query(CallbackDataFilter("flt:text"))
    async def show_text_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "Текстовые фильтры\n\nВыберите фильтр для теста:",
            filter_text_user_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:txt:regexp"))
    async def start_regexp_test(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_email_regexp)
        await safe_edit(
            event,
            bot,
            'Тест RegexpFilter(r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$")\n\n'
            "Отправьте email-адрес для проверки.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:txt:tag"))
    async def start_tag_test(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_tag)
        await safe_edit(
            event,
            bot,
            'Тест TagFilter(["hello", "hi", "hey"])\n\n'
            "Отправьте одно из слов: hello, hi, hey.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:txt:cmd"))
    async def start_cmd_test(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_command)
        await safe_edit(
            event,
            bot,
            'Тест CommandFilter("demo")\n\n' "Отправьте команду /demo.",
            back_to_main_kb(),
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_email_regexp, storage),
        RegexpFilter(r"^[\w.+-]+@[\w-]+\.[\w.]+$"),
    )
    async def regexp_match(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"RegexpFilter сработал! Обнаружен email: {event.text}",
            inline_keyboard_markup=filter_text_user_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_email_regexp, storage))
    async def fallback_regexp(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="Не похоже на email. Попробуйте снова или /cancel.",
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_tag, storage),
        TagFilter(["hello", "hi", "hey"]),
    )
    async def tag_match(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"TagFilter сработал! Вы сказали: {event.text}",
            inline_keyboard_markup=filter_text_user_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_tag, storage))
    async def fallback_tag(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="TagFilter не сработал. Отправьте hello, hi или hey. Или /cancel.",
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_command, storage),
        CommandFilter("demo"),
    )
    async def command_match(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="CommandFilter сработал! Команда /demo получена.",
            inline_keyboard_markup=filter_text_user_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_command, storage))
    async def fallback_command(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="Ожидается команда /demo. Или /cancel для выхода.",
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
    async def test_and_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_and)
        await safe_edit(
            event,
            bot,
            "Тест AND: ReplyFilter() & FileFilter()\n\n"
            "Ответьте на любое сообщение и прикрепите файл к ответу.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:comp:or"))
    async def test_or_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_or)
        await safe_edit(
            event,
            bot,
            "Тест OR: FileFilter() | VoiceFilter()\n\n"
            "Отправьте файл или голосовое сообщение.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:comp:not"))
    async def test_not_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_not)
        await safe_edit(
            event,
            bot,
            "Тест NOT: ~StickerFilter()\n\n"
            "Отправьте любое сообщение, которое НЕ является стикером.",
            back_to_main_kb(),
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_and, storage),
        ReplyFilter() & FileFilter(),
    )
    async def got_and(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="AND-фильтр сработал! Ответ с файлом обнаружен.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_and, storage))
    async def fallback_and(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id,
            "Нужен ответ на сообщение с прикрепленным файлом. Или /cancel.",
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_or, storage),
        FileFilter() | VoiceFilter(),
    )
    async def got_or(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="OR-фильтр сработал! Файл или голосовое обнаружено.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_or, storage))
    async def fallback_or(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается файл или голосовое сообщение. Или /cancel."
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_not, storage), ~StickerFilter()
    )
    async def got_not(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text="NOT-фильтр сработал! Сообщение не является стикером.",
            inline_keyboard_markup=filter_composite_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_not, storage))
    async def fallback_not(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id,
            "Вы отправили стикер -- NOT-фильтр его отклонит. Отправьте что-то другое. Или /cancel.",
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
    async def test_regexp_parts(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_regexp_parts)
        await safe_edit(
            event,
            bot,
            'Тест RegexpTextPartsFilter(r"https?://\\S+")\n\n'
            "Перешлите или ответьте на сообщение, содержащее URL.",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:adv:nick"))
    async def test_nick_parts(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        bot_info = await bot.get_self()
        nick = bot_info.nick or "unknown"
        await fsm_context.set_state(FilterDemoStates.waiting_for_nick_parts)
        await fsm_context.update_data(bot_nick=nick)
        await safe_edit(
            event,
            bot,
            f'Тест MessageTextPartFromNickFilter("{nick}")\n\n'
            f"Перешлите или ответьте на сообщение от этого бота (@{nick}).",
            back_to_main_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:adv:cbregexp"))
    async def show_cbregexp_info(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event,
            bot,
            "CallbackDataRegexpFilter\n\n"
            "Этот фильтр уже используется во всем боте для маршрутизации "
            "callback-запросов. Все кнопки с префиксами btn:, nav:, fmt:, wzb: и т.д. "
            'обрабатываются именно через CallbackDataRegexpFilter(r"^prefix:").',
            filter_advanced_kb(),
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_regexp_parts, storage),
        RegexpTextPartsFilter(r"https?://\S+"),
    )
    async def got_regexp_parts(
        event: NewMessageEvent, bot: Bot, fsm_context: FSMContext
    ):
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

    # -- Merged from filters_new: TextFilter, FileTypeFilter, FromUserFilter, ChatTypeFilter, ChatIdFilter --

    @dp.callback_query(CallbackDataFilter("flt:text_filter"))
    async def test_text_filter(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_text_filter)
        await safe_edit(
            event,
            bot,
            "Тест TextFilter\n\n"
            "Отправьте текстовое сообщение. TextFilter пропускает сообщения "
            "с непустым текстом (пробелы не считаются).",
            filter_text_user_kb(),
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_text_filter, storage), TextFilter()
    )
    async def got_text_filter(
        event: NewMessageEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f'TextFilter сработал!\n\nТекст: "{event.text}"',
            inline_keyboard_markup=filter_text_user_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:fromuser"))
    async def test_from_user(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        user_id = event.from_.user_id if event.from_ else "unknown"
        await fsm_context.set_state(FilterDemoStates.waiting_for_from_user)
        await fsm_context.update_data(target_user_id=user_id)
        await safe_edit(
            event,
            bot,
            f'Тест FromUserFilter("{user_id}")\n\n'
            f"Фильтр настроен на ваш user_id. Отправьте любое сообщение для проверки.",
            filter_text_user_kb(),
        )

    # FromUserFilter uses manual call because the user_id is dynamic
    # Idiomatic usage: @dp.message(FromUserFilter("some_fixed_user_id"))
    @dp.message(StateFilter(FilterDemoStates.waiting_for_from_user, storage))
    async def got_from_user(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        data = await fsm_context.get_data()
        target_id = data.get("target_user_id", "")
        flt = FromUserFilter(target_id)
        matched = flt(event)
        await fsm_context.clear()
        sender_id = event.from_.user_id if event.from_ else "unknown"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=(
                f'FromUserFilter("{target_id}")\n\n'
                f"Отправитель: {sender_id}\n"
                f"Совпадение: {matched}"
            ),
            inline_keyboard_markup=filter_text_user_kb(),
        )

    # -- Advanced: ChatTypeFilter (no state needed) --
    @dp.callback_query(CallbackDataFilter("flt:chattype"))
    async def test_chat_type(event: CallbackQueryEvent, bot: Bot):
        chat = event.chat
        chat_type = chat.type if chat else "unknown"
        await safe_edit(
            event,
            bot,
            f"ChatTypeFilter\n\n"
            f"Текущий тип чата: {chat_type}\n\n"
            f"ChatTypeFilter(ChatType.PRIVATE) -- сработает только в личных сообщениях.\n"
            f"ChatTypeFilter(ChatType.GROUP) -- сработает только в группе.\n"
            f"ChatTypeFilter([ChatType.GROUP, ChatType.CHANNEL]) -- группа или канал.",
            filter_advanced_kb(),
        )

    # ChatIdFilter uses manual call because the chat_id is dynamic
    # Idiomatic usage: @dp.callback_query(ChatIdFilter("some_fixed_chat_id"))
    @dp.callback_query(CallbackDataFilter("flt:chatid"))
    async def test_chat_id(event: CallbackQueryEvent, bot: Bot):
        chat_id = event.chat.chat_id if event.chat else "unknown"
        flt = ChatIdFilter(chat_id)
        matched = flt(event)
        await safe_edit(
            event,
            bot,
            f"ChatIdFilter\n\n"
            f"Текущий chat_id: {chat_id}\n"
            f'ChatIdFilter("{chat_id}") -- совпадение: {matched}\n\n'
            f"Используйте для ограничения бота конкретными чатами.",
            filter_advanced_kb(),
        )

    @dp.callback_query(CallbackDataFilter("flt:filetype"))
    async def test_filetype(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(FilterDemoStates.waiting_for_filetype)
        await safe_edit(
            event,
            bot,
            'Тест FileTypeFilter(["image", "audio", "video"])\n\n'
            "Отправьте изображение, аудио или видео.",
            filter_advanced_kb(),
        )

    @dp.message(
        StateFilter(FilterDemoStates.waiting_for_filetype, storage),
        FileTypeFilter(["image", "audio", "video"]),
    )
    async def got_filetype(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        from vk_teams_async_bot.types.message import FilePart

        matched_types = [
            p.payload.type
            for p in (event.parts or [])
            if isinstance(p, FilePart) and p.payload.type in ("image", "audio", "video")
        ]
        type_str = ", ".join(matched_types) if matched_types else "unknown"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"FileTypeFilter сработал!\n\nТип файла: {type_str}",
            inline_keyboard_markup=filter_advanced_kb(),
        )

    @dp.message(StateFilter(FilterDemoStates.waiting_for_filetype, storage))
    async def fallback_filetype(event: NewMessageEvent, bot: Bot):
        await bot.send_text(
            event.chat.chat_id, "Ожидается изображение, аудио или видео. Или /cancel."
        )

    # -- MentionUserFilter (Phase 4.1) --
    @dp.callback_query(CallbackDataFilter("flt:mention_user"))
    async def test_mention_user(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        bot_info = await bot.get_self()
        nick = bot_info.nick or "unknown"
        user_id = bot_info.user_id
        await fsm_context.set_state(FilterDemoStates.waiting_for_mention_user)
        await fsm_context.update_data(bot_nick=nick, bot_user_id=user_id)
        await safe_edit(
            event,
            bot,
            f'Тест MentionUserFilter("{user_id}")\n\n'
            f"Отправьте сообщение с упоминанием @{nick}.",
            filter_advanced_kb(),
        )

    # MentionUserFilter uses manual call because the nick is dynamic
    # Idiomatic usage: @dp.message(MentionUserFilter("fixed_nick"))
    @dp.message(StateFilter(FilterDemoStates.waiting_for_mention_user, storage))
    async def got_mention_user(
        event: NewMessageEvent, bot: Bot, fsm_context: FSMContext
    ):
        data = await fsm_context.get_data()
        nick = data.get("bot_nick", "")
        user_id = data.get("bot_user_id", "")
        flt = MentionUserFilter(user_id)
        if flt(event):
            await fsm_context.clear()
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"MentionUserFilter сработал! Упоминание @{nick} обнаружено.",
                inline_keyboard_markup=filter_advanced_kb(),
            )
        else:
            await bot.send_text(
                chat_id=event.chat.chat_id,
                text=f"MentionUserFilter не сработал. Упомяните @{nick} в сообщении. Или /cancel.",
            )
