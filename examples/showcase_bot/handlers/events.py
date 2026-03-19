from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackQueryEvent,
    DeletedMessageEvent,
    Dispatcher,
    EditedMessageEvent,
    LeftChatMembersEvent,
    NewChatMembersEvent,
    PinnedMessageEvent,
    UnpinnedMessageEvent,
)

from ..keyboards import events_info_kb
from .utils import safe_edit

_watching_chats: set[str] = set()


def register_events_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:evt"))
    async def show_events(event: CallbackQueryEvent, bot: Bot):
        _watching_chats.add(event.chat.chat_id)
        text = (
            "События чата\n\n"
            "Бот отслеживает такие события:\n"
            "- Редактирование сообщений\n"
            "- Удаление сообщений\n"
            "- Закрепление сообщений\n"
            "- Открепление сообщений\n"
            "- Новые участники чата\n"
            "- Выход участников из чата\n\n"
            "Попробуйте отредактировать, удалить или закрепить сообщение "
            "в этом чате, чтобы увидеть реакцию бота."
        )
        await safe_edit(event, bot, text, events_info_kb())

    @dp.callback_query(CallbackDataFilter("evt:stop"))
    async def stop_watching(event: CallbackQueryEvent, bot: Bot):
        _watching_chats.discard(event.chat.chat_id)
        await safe_edit(
            event,
            bot,
            "Отслеживание событий остановлено.",
            events_info_kb(),
        )

    @dp.edited_message()
    async def on_edited(event: EditedMessageEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Обнаружено редактирование сообщения (msg_id: {event.msg_id})",
        )

    @dp.deleted_message()
    async def on_deleted(event: DeletedMessageEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Обнаружено удаление сообщения (msg_id: {event.msg_id})",
        )

    @dp.pinned_message()
    async def on_pinned(event: PinnedMessageEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Сообщение закреплено (msg_id: {event.msg_id})",
        )

    @dp.unpinned_message()
    async def on_unpinned(event: UnpinnedMessageEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Сообщение откреплено (msg_id: {event.msg_id})",
        )

    @dp.new_chat_members()
    async def on_new_members(event: NewChatMembersEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        names = ", ".join(m.first_name or m.user_id for m in event.new_members)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"Добро пожаловать, {names}!",
        )

    @dp.left_chat_members()
    async def on_left_members(event: LeftChatMembersEvent, bot: Bot):
        if event.chat.chat_id not in _watching_chats:
            return
        names = ", ".join(m.first_name or m.user_id for m in event.left_members)
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=f"До свидания, {names}!",
        )
