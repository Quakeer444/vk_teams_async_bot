import asyncio
import logging
import os
from typing import Any

from vk_teams_async_bot import (
    BaseMiddleware,
    Bot,
    CommandFilter,
    Dispatcher,
    NewMessageEvent,
)
from vk_teams_async_bot.types.event import BaseEvent, RawUnknownEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()
logger = logging.getLogger(__name__)


@dp.message(CommandFilter("/start"))
async def cmd_start(event: NewMessageEvent, bot: Bot):
    await bot.send_text(chat_id=event.chat.chat_id, text="Hello")


class AccessMiddleware(BaseMiddleware):
    """Check user/group access rights before processing."""

    async def __call__(self, handler, event, data):
        allowed_chats = [
            "id@chat.agent",
        ]

        if isinstance(event, (BaseEvent,)) and hasattr(event, "chat"):
            if event.chat.chat_id not in allowed_chats:
                bot = data["bot"]
                text = f"Does not have rights to use the bot - {event.chat.chat_id}"
                await bot.send_text(chat_id=event.chat.chat_id, text=text)
                return

        return await handler(event, data)


class UserRoleMiddleware(BaseMiddleware):
    """Inject user role into the data dict for use in handlers."""

    async def __call__(self, handler, event, data):
        roles = {
            "id@chat.agent": "admin",
        }

        if isinstance(event, (BaseEvent,)) and hasattr(event, "chat"):
            data["role"] = roles.get(event.chat.chat_id)
            logger.debug(
                "UserRoleMiddleware role for %s - %s",
                event.chat.chat_id,
                data.get("role"),
            )

        return await handler(event, data)


dp.add_middleware(AccessMiddleware())
dp.add_middleware(UserRoleMiddleware())


async def main():
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
