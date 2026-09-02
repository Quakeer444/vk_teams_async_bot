"""Thread-related API methods."""

from __future__ import annotations

import logging

from vk_teams_async_bot.types.response import (
    OkResponse,
    ThreadResponse,
    ThreadSubscribersResponse,
)

from ._helpers import bool_str as _bool_str
from .base import BaseMethods

logger = logging.getLogger(__name__)


class ThreadMethods(BaseMethods):
    """Mixin providing /threads/* API methods."""

    async def create_thread(
        self,
        chat_id: str,
        msg_id: str | int,
    ) -> ThreadResponse:
        """Create a thread on a message in a chat.

        The bot must be a member of the chat where the thread is created.

        Endpoint: GET /threads/add
        """
        logger.debug("create_thread: chat_id=%s, msg_id=%s", chat_id, msg_id)
        raw = await self._session.get(
            "/threads/add",
            chatId=chat_id,
            msgId=msg_id,
        )
        return ThreadResponse.model_validate(raw)

    async def set_thread_autosubscribe(
        self,
        chat_id: str,
        enable: bool,
        *,
        with_existing: bool | None = None,
    ) -> OkResponse:
        """Enable/disable automatic subscription to all threads in a chat.

        The bot must be a member of the chat.

        Endpoint: GET /threads/autosubscribe
        """
        logger.debug("set_thread_autosubscribe: chat_id=%s, enable=%s", chat_id, enable)
        raw = await self._session.get(
            "/threads/autosubscribe",
            chatId=chat_id,
            enable=_bool_str(enable),
            withExisting=_bool_str(with_existing),
        )
        return OkResponse.model_validate(raw)

    async def get_thread_subscribers(
        self,
        thread_id: str,
        *,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> ThreadSubscribersResponse:
        """Get thread subscribers list (with cursor pagination).

        Endpoint: GET /threads/subscribers/get
        """
        raw = await self._session.get(
            "/threads/subscribers/get",
            threadId=thread_id,
            pageSize=page_size,
            cursor=cursor,
        )
        return ThreadSubscribersResponse.model_validate(raw)
