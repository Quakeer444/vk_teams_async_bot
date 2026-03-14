import asyncio
import os
from typing import Annotated

import aiohttp

from vk_teams_async_bot import Bot, Dispatcher, NewMessageEvent

bot = Bot(bot_token=os.environ["BOT_TOKEN"])
dp = Dispatcher()


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


@dp.message()
async def echo_handler(
    event: NewMessageEvent,
    bot: Bot,
    rules: list_rules,
    list_permissons: list_permissions,
    session: Annotated[aiohttp.ClientSession, gen],
):
    async with session.get(url="http://example.com") as res:
        print(res.status)
        print(rules)
        print(list_permissons)
    await bot.send_text(chat_id=event.chat.chat_id, text=event.text or "")


async def main():
    bot.depends.append(gen)
    bot.depends.append(list_rules)
    bot.depends.append(list_permissions)
    async with bot:
        await bot.start_polling(dp)


if __name__ == "__main__":
    asyncio.run(main())
