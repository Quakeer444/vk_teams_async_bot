import asyncio
import logging

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.filter import Filter
from vk_teams_async_bot.handler import CommandHandler
from vk_teams_async_bot.middleware import Middleware

app = Bot(bot_token="TOKEN", url="URL")
logger = logging.getLogger(__name__)


async def cmd_start(event: Event, bot: Bot):
    await bot.send_text(chat_id=event.chat.chatId, text="Hello")


app.dispatcher.add_handler(
    CommandHandler(callback=cmd_start, filters=Filter.command("/start")),
)


class AccessMiddleware(Middleware):
    """
    Проверить права доступа пользователя или группы на использования бота
    """

    async def handle(self, event, bot):
        allowed_chats = [
            "id@chat.agent",
        ]

        if event.chat.chatId not in allowed_chats:
            text = f"Does not have rights to use the bot - {event.chat.chatId}"
            await bot.send_text(chat_id=event.chat.chatId, text=text)
            raise PermissionError(text)
        return event


class UserRoleMiddleware(Middleware):
    """
    Проверить права пользователя (из словаря, бд и т.д.) и добавить эти данные в событие Event,
    с которыми можно работать в каждом handler
    """

    async def handle(self, event, bot):
        roles = {
            "id@chat.agent": "admin",
        }
        event.middleware_data.update({"role": roles.get(event.chat.chatId)})
        logger.debug(
            "UserRoleMiddleware role for {chatID} - {role}".format(
                chatID=event.chat.chatId, role=event.middleware_data.get("role")
            )
        )
        return event


async def main():
    app.dispatcher.middlewares = [AccessMiddleware(), UserRoleMiddleware()]

    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
