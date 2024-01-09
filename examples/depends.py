import asyncio
from typing import Annotated

import aiohttp

from local_.config import env
from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.handler import MessageHandler

app = Bot(bot_token=env.TEST_BOT_TOKEN.get_secret_value())


async def create_session():
    session = aiohttp.ClientSession()
    return session


async def gen():
    sess = await create_session()
    try:
        print("start session")
        yield sess
    finally:
        print("finish session")
        await sess.close()


async def list_rules():
    return ["1", "2", "3", "4", "5", "6"]


def list_permissions():
    return ["Success"]


async def echo_handler(
    event: Event,
    bot: Bot,
    rules: list_rules,
    list_permissons: list_permissions,
    session: Annotated[aiohttp.ClientSession, gen],
):
    async with session.get(url="http://example.com") as res:
        print(res.status)
        print(rules)
        print(list_permissons)
    await bot.send_text(chat_id=event.chat.chatId, text=event.text)


app.dispatcher.add_handler(
    MessageHandler(
        callback=echo_handler,
    )
)


async def main():
    app.depends.append(gen)
    app.depends.append(list_rules)
    app.depends.append(list_permissions)
    await app.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
