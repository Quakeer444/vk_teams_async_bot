"""Chat-related API methods."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import FormData
from pydantic import TypeAdapter

from vk_teams_async_bot.types.chat import ChatInfoResponse
from vk_teams_async_bot.types.enums import ChatAction
from vk_teams_async_bot.types.response import (
    AdminsResponse,
    ChatCreateResponse,
    MembersResponse,
    OkResponse,
    OkWithDescriptionResponse,
    PartialSuccessResponse,
    UsersResponse,
)

from .base import BaseMethods

_chat_info_adapter = TypeAdapter(ChatInfoResponse)


def _serialize_members(members: list[str]) -> str:
    """Convert a list of user IDs to the API-expected JSON format."""
    return json.dumps([{"sn": uid} for uid in members])


def _bool_str(value: bool | None) -> str | None:
    """Convert a Python bool to ``"true"``/``"false"`` string."""
    if value is None:
        return None
    return "true" if value else "false"


def _serialize_actions(actions: list[ChatAction] | list[str]) -> str:
    """Serialize chat actions as a comma-separated string."""
    return ",".join(str(a) for a in actions)


class ChatMethods(BaseMethods):
    """Mixin providing /chats/* API methods."""

    async def create_chat(
        self,
        name: str,
        *,
        about: str | None = None,
        rules: str | None = None,
        members: list[str] | None = None,
        public: bool | None = None,
        default_role: str | None = None,
        join_moderation: bool | None = None,
    ) -> ChatCreateResponse:
        """Create a new chat.

        Endpoint: GET /chats/createChat
        """
        raw = await self._session.get(
            "/chats/createChat",
            name=name,
            about=about,
            rules=rules,
            members=_serialize_members(members) if members else None,
            public=_bool_str(public),
            defaultRole=default_role,
            joinModeration=_bool_str(join_moderation),
        )
        return ChatCreateResponse.model_validate(raw)

    async def set_chat_avatar(
        self,
        chat_id: str,
        image: str | tuple,
    ) -> OkWithDescriptionResponse:
        """Set chat avatar.

        ``image`` can be a file path (str) or a (filename, file_obj, content_type) tuple.

        Endpoint: POST /chats/avatar/set
        """
        form = FormData(quote_fields=False)
        if isinstance(image, str):
            with open(image, "rb") as fh:
                content = fh.read()
            form.add_field("image", content, filename=image)
        elif isinstance(image, tuple):
            filename, file_obj, content_type = image
            form.add_field(
                "image",
                file_obj,
                filename=filename,
                content_type=content_type,
            )
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")

        raw = await self._session.post(
            "/chats/avatar/set",
            data=form,
            chatId=chat_id,
        )
        return OkWithDescriptionResponse.model_validate(raw)

    async def add_chat_members(
        self,
        chat_id: str,
        members: list[str],
    ) -> PartialSuccessResponse:
        """Add members to a chat.

        Endpoint: GET /chats/members/add
        """
        raw = await self._session.get(
            "/chats/members/add",
            chatId=chat_id,
            members=_serialize_members(members),
        )
        return PartialSuccessResponse.model_validate(raw)

    async def delete_chat_members(
        self,
        chat_id: str,
        members: list[str],
    ) -> OkResponse:
        """Delete members from a chat.

        Endpoint: GET /chats/members/delete
        """
        raw = await self._session.get(
            "/chats/members/delete",
            chatId=chat_id,
            members=_serialize_members(members),
        )
        return OkResponse.model_validate(raw)

    async def send_chat_actions(
        self,
        chat_id: str,
        actions: list[ChatAction] | list[str],
    ) -> OkResponse:
        """Send chat actions (e.g., typing indicator).

        Endpoint: GET /chats/sendActions
        """
        raw = await self._session.get(
            "/chats/sendActions",
            chatId=chat_id,
            actions=_serialize_actions(actions),
        )
        return OkResponse.model_validate(raw)

    async def get_chat_info(
        self,
        chat_id: str,
    ) -> Any:
        """Get chat info (discriminated by ``type`` field).

        Returns ``ChatInfoPrivate``, ``ChatInfoGroup``, or
        ``ChatInfoChannel`` depending on the chat type.

        Endpoint: GET /chats/getInfo
        """
        raw = await self._session.get(
            "/chats/getInfo",
            chatId=chat_id,
        )
        return _chat_info_adapter.validate_python(raw)

    async def get_chat_admins(
        self,
        chat_id: str,
    ) -> AdminsResponse:
        """Get chat admins list.

        Endpoint: GET /chats/getAdmins
        """
        raw = await self._session.get(
            "/chats/getAdmins",
            chatId=chat_id,
        )
        return AdminsResponse.model_validate(raw)

    async def get_chat_members(
        self,
        chat_id: str,
        *,
        cursor: str | None = None,
    ) -> MembersResponse:
        """Get chat members list (with cursor pagination).

        Endpoint: GET /chats/getMembers
        """
        raw = await self._session.get(
            "/chats/getMembers",
            chatId=chat_id,
            cursor=cursor,
        )
        return MembersResponse.model_validate(raw)

    async def get_blocked_users(
        self,
        chat_id: str,
    ) -> UsersResponse:
        """Get blocked users list.

        Endpoint: GET /chats/getBlockedUsers
        """
        raw = await self._session.get(
            "/chats/getBlockedUsers",
            chatId=chat_id,
        )
        return UsersResponse.model_validate(raw)

    async def get_pending_users(
        self,
        chat_id: str,
    ) -> UsersResponse:
        """Get pending users list.

        Endpoint: GET /chats/getPendingUsers
        """
        raw = await self._session.get(
            "/chats/getPendingUsers",
            chatId=chat_id,
        )
        return UsersResponse.model_validate(raw)

    async def block_user(
        self,
        chat_id: str,
        user_id: str,
        *,
        del_last_messages: bool | None = None,
    ) -> OkResponse:
        """Block a user in chat.

        Endpoint: GET /chats/blockUser
        """
        raw = await self._session.get(
            "/chats/blockUser",
            chatId=chat_id,
            userId=user_id,
            delLastMessages=_bool_str(del_last_messages),
        )
        return OkResponse.model_validate(raw)

    async def unblock_user(
        self,
        chat_id: str,
        user_id: str,
    ) -> OkResponse:
        """Unblock a user in chat.

        Endpoint: GET /chats/unblockUser
        """
        raw = await self._session.get(
            "/chats/unblockUser",
            chatId=chat_id,
            userId=user_id,
        )
        return OkResponse.model_validate(raw)

    async def resolve_pending(
        self,
        chat_id: str,
        approve: bool,
        *,
        user_id: str | None = None,
        everyone: bool | None = None,
    ) -> OkResponse:
        """Resolve pending users (approve or reject).

        Exactly one of ``user_id`` or ``everyone`` must be provided.

        Endpoint: GET /chats/resolvePending
        """
        has_user = user_id is not None
        has_everyone = everyone is not None
        if has_user == has_everyone:
            raise ValueError(
                "Exactly one of user_id or everyone must be provided"
            )

        raw = await self._session.get(
            "/chats/resolvePending",
            chatId=chat_id,
            approve=_bool_str(approve),
            userId=user_id,
            everyone=_bool_str(everyone),
        )
        return OkResponse.model_validate(raw)

    async def set_chat_title(
        self,
        chat_id: str,
        title: str,
    ) -> OkResponse:
        """Set chat title.

        Endpoint: GET /chats/setTitle
        """
        raw = await self._session.get(
            "/chats/setTitle",
            chatId=chat_id,
            title=title,
        )
        return OkResponse.model_validate(raw)

    async def set_chat_about(
        self,
        chat_id: str,
        about: str,
    ) -> OkResponse:
        """Set chat description.

        Endpoint: GET /chats/setAbout
        """
        raw = await self._session.get(
            "/chats/setAbout",
            chatId=chat_id,
            about=about,
        )
        return OkResponse.model_validate(raw)

    async def set_chat_rules(
        self,
        chat_id: str,
        rules: str,
    ) -> OkResponse:
        """Set chat rules.

        Endpoint: GET /chats/setRules
        """
        raw = await self._session.get(
            "/chats/setRules",
            chatId=chat_id,
            rules=rules,
        )
        return OkResponse.model_validate(raw)

    async def pin_message(
        self,
        chat_id: str,
        msg_id: str | int,
    ) -> OkResponse:
        """Pin a message in chat.

        Endpoint: GET /chats/pinMessage
        """
        raw = await self._session.get(
            "/chats/pinMessage",
            chatId=chat_id,
            msgId=msg_id,
        )
        return OkResponse.model_validate(raw)

    async def unpin_message(
        self,
        chat_id: str,
        msg_id: str | int,
    ) -> OkResponse:
        """Unpin a message in chat.

        Endpoint: GET /chats/unpinMessage
        """
        raw = await self._session.get(
            "/chats/unpinMessage",
            chatId=chat_id,
            msgId=msg_id,
        )
        return OkResponse.model_validate(raw)
