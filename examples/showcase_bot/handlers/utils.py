from vk_teams_async_bot import Bot, CallbackQueryEvent


async def safe_edit(
    event: CallbackQueryEvent, bot: Bot, text: str, keyboard=None, **kwargs
):
    await bot.answer_callback_query(query_id=event.query_id)
    if event.message:
        await bot.edit_text(
            chat_id=event.chat.chat_id,
            msg_id=event.message.msg_id,
            text=text,
            inline_keyboard_markup=keyboard,
            **kwargs,
        )
    else:
        await bot.send_text(
            chat_id=event.chat.chat_id,
            text=text,
            inline_keyboard_markup=keyboard,
            **kwargs,
        )


def progress_bar(step: int, total: int) -> str:
    filled = step
    empty = total - step
    bar = "#" * filled + "-" * empty
    return f"[{bar}] {step}/{total}"
