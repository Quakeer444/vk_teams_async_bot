from vk_teams_async_bot import (
    APIError,
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    ChatIdFilter,
    ChatTypeFilter,
    Dispatcher,
    FileTypeFilter,
    FromUserFilter,
    FSMContext,
    NewMessageEvent,
    StateFilter,
    TextFilter,
)
from vk_teams_async_bot.fsm.storage.base import BaseStorage

from ..keyboards_extra import new_filters_menu_kb
from ..states import NewFilterDemoStates


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


def register_new_filters_handlers(dp: Dispatcher, storage: BaseStorage) -> None:
    @dp.callback_query(CallbackDataFilter("menu:flt2"))
    async def show_new_filters(event: CallbackQueryEvent, bot: Bot):
        await safe_edit(
            event, bot,
            "Новые фильтры\n\n"
            "Фильтры, добавленные в библиотеку.\n"
            "Выберите фильтр для теста:",
            new_filters_menu_kb(),
        )

    # -- ChatTypeFilter (no state needed) --
    @dp.callback_query(CallbackDataFilter("flt2:chattype"))
    async def test_chat_type(event: CallbackQueryEvent, bot: Bot):
        chat = event.chat
        chat_type = chat.type if chat else "unknown"
        await safe_edit(
            event, bot,
            f"ChatTypeFilter\n\n"
            f"Текущий тип чата: {chat_type}\n\n"
            f"ChatTypeFilter(ChatType.PRIVATE) -- сработает только в личных сообщениях.\n"
            f"ChatTypeFilter(ChatType.GROUP) -- сработает только в группе.\n"
            f"ChatTypeFilter([ChatType.GROUP, ChatType.CHANNEL]) -- группа или канал.",
            new_filters_menu_kb(),
        )

    # -- ChatIdFilter (no state needed) --
    @dp.callback_query(CallbackDataFilter("flt2:chatid"))
    async def test_chat_id(event: CallbackQueryEvent, bot: Bot):
        chat_id = event.chat.chat_id if event.chat else "unknown"
        flt = ChatIdFilter(chat_id)
        matched = flt(event)
        await safe_edit(
            event, bot,
            f"ChatIdFilter\n\n"
            f"Текущий chat_id: {chat_id}\n"
            f"ChatIdFilter(\"{chat_id}\") -- совпадение: {matched}\n\n"
            f"Используйте для ограничения бота конкретными чатами.",
            new_filters_menu_kb(),
        )

    # -- TextFilter (state needed) --
    @dp.callback_query(CallbackDataFilter("flt2:text"))
    async def test_text_filter(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(NewFilterDemoStates.waiting_for_text_filter)
        await safe_edit(
            event, bot,
            "Тест TextFilter\n\n"
            "Отправьте текстовое сообщение. TextFilter пропускает сообщения "
            "с непустым текстом (пробелы не считаются).",
            new_filters_menu_kb(),
        )

    @dp.message(StateFilter(NewFilterDemoStates.waiting_for_text_filter, storage), TextFilter())
    async def got_text_filter(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"TextFilter сработал!\n\nТекст: \"{event.text}\"",
            inline_keyboard_markup=new_filters_menu_kb(),
        )

    # -- FileTypeFilter (state needed) --
    @dp.callback_query(CallbackDataFilter("flt2:filetype"))
    async def test_filetype(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.set_state(NewFilterDemoStates.waiting_for_filetype)
        await safe_edit(
            event, bot,
            "Тест FileTypeFilter([\"image\", \"audio\", \"video\"])\n\n"
            "Отправьте изображение, аудио или видео.",
            new_filters_menu_kb(),
        )

    @dp.message(
        StateFilter(NewFilterDemoStates.waiting_for_filetype, storage),
        FileTypeFilter(["image", "audio", "video"]),
    )
    async def got_filetype(event: NewMessageEvent, bot: Bot, fsm_context: FSMContext):
        await fsm_context.clear()
        from vk_teams_async_bot.types.message import FilePart
        matched_types = [
            p.payload.type for p in (event.parts or [])
            if isinstance(p, FilePart) and p.payload.type in ("image", "audio", "video")
        ]
        type_str = ", ".join(matched_types) if matched_types else "unknown"
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"FileTypeFilter сработал!\n\nТип файла: {type_str}",
            inline_keyboard_markup=new_filters_menu_kb(),
        )

    # -- FromUserFilter (state needed) --
    @dp.callback_query(CallbackDataFilter("flt2:fromuser"))
    async def test_from_user(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        user_id = event.from_.user_id if event.from_ else "unknown"
        await fsm_context.set_state(NewFilterDemoStates.waiting_for_from_user)
        await fsm_context.update_data(target_user_id=user_id)
        await safe_edit(
            event, bot,
            f"Тест FromUserFilter(\"{user_id}\")\n\n"
            f"Фильтр настроен на ваш user_id. Отправьте любое сообщение для проверки.",
            new_filters_menu_kb(),
        )

    @dp.message(StateFilter(NewFilterDemoStates.waiting_for_from_user, storage))
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
                f"FromUserFilter(\"{target_id}\")\n\n"
                f"Отправитель: {sender_id}\n"
                f"Совпадение: {matched}"
            ),
            inline_keyboard_markup=new_filters_menu_kb(),
        )
