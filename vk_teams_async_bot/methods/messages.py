"""Message-related API methods."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aiohttp import FormData

from vk_teams_async_bot.types.enums import ParseMode
from vk_teams_async_bot.types.response import (
    FileUploadResponse,
    MessageResponse,
    OkResponse,
)

from .base import BaseMethods


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_keyboard(
    markup: Any | None,
) -> str | None:
    """Convert an InlineKeyboardMarkup (or raw string) to a JSON string."""
    if markup is None:
        return None
    if isinstance(markup, str):
        return markup
    # InlineKeyboardMarkup or any object with .to_json()
    return markup.to_json()


def _serialize_format(fmt: Any | None) -> str | None:
    """Serialize a Format object, dict, or string for the ``format`` param."""
    if fmt is None:
        return None
    if isinstance(fmt, str):
        return fmt
    # Format object
    if hasattr(fmt, "to_json"):
        return fmt.to_json()
    # Plain dict
    if isinstance(fmt, dict):
        return json.dumps(fmt)
    raise TypeError(f"Unsupported format_ type: {type(fmt)}")


def _serialize_msg_ids(value: Any | None) -> Any | None:
    """Serialize msg_id lists as JSON array strings."""
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps(value)
    return value


def _validate_reply_forward(
    reply_msg_id: Any | None,
    forward_chat_id: str | None,
    forward_msg_id: Any | None,
) -> None:
    """Enforce mutual exclusion between reply and forward params."""
    has_reply = reply_msg_id is not None
    has_forward_chat = forward_chat_id is not None
    has_forward_msg = forward_msg_id is not None

    if has_reply and (has_forward_chat or has_forward_msg):
        raise ValueError(
            "replyMsgId and forwardChatId/forwardMsgId are mutually exclusive"
        )
    if has_forward_chat != has_forward_msg:
        raise ValueError(
            "forwardChatId and forwardMsgId must be provided together"
        )


def _validate_parse_format(
    parse_mode: ParseMode | None,
    format_: Any | None,
) -> None:
    """Enforce mutual exclusion between parseMode and format."""
    if parse_mode is not None and format_ is not None:
        raise ValueError("parseMode and format are mutually exclusive")


def _validate_file_source(
    file_id: str | None,
    file: Any | None,
) -> None:
    """Exactly one of file_id or file must be provided."""
    if file_id is not None and file is not None:
        raise ValueError("file_id and file are mutually exclusive")
    if file_id is None and file is None:
        raise ValueError("One of file_id or file must be provided")


def _build_form_data(
    file: str | Path | tuple,
    field_name: str = "file",
) -> FormData:
    """Build aiohttp FormData for a file upload.

    ``file`` can be:
      - str / Path  -- path to a file on disk (read synchronously)
      - tuple(filename, file_obj, content_type) -- already-open file
    """
    form = FormData(quote_fields=False)
    if isinstance(file, (str, Path)):
        path = Path(file)
        with open(path, "rb") as fh:
            content = fh.read()
        form.add_field(field_name, content, filename=path.name)
    elif isinstance(file, tuple):
        filename, file_obj, content_type = file
        form.add_field(
            field_name,
            file_obj,
            filename=filename,
            content_type=content_type,
        )
    else:
        raise TypeError(f"Unsupported file type: {type(file)}")
    return form


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------


class MessageMethods(BaseMethods):
    """Mixin providing /messages/* API methods."""

    async def send_text(
        self,
        chat_id: str,
        text: str,
        *,
        reply_msg_id: Any | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: Any | None = None,
        inline_keyboard_markup: Any | None = None,
        format_: Any | None = None,
        parse_mode: ParseMode | None = None,
    ) -> MessageResponse:
        """Send a text message.

        Endpoint: GET /messages/sendText
        """
        _validate_reply_forward(reply_msg_id, forward_chat_id, forward_msg_id)
        _validate_parse_format(parse_mode, format_)

        raw = await self._session.get(
            "/messages/sendText",
            chatId=chat_id,
            text=text,
            replyMsgId=_serialize_msg_ids(reply_msg_id),
            forwardChatId=forward_chat_id,
            forwardMsgId=_serialize_msg_ids(forward_msg_id),
            inlineKeyboardMarkup=_serialize_keyboard(inline_keyboard_markup),
            format=_serialize_format(format_),
            parseMode=parse_mode.value if parse_mode else None,
        )
        return MessageResponse.model_validate(raw)

    async def send_file(
        self,
        chat_id: str,
        *,
        file_id: str | None = None,
        file: str | Path | tuple | None = None,
        caption: str | None = None,
        reply_msg_id: Any | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: Any | None = None,
        inline_keyboard_markup: Any | None = None,
        format_: Any | None = None,
        parse_mode: ParseMode | None = None,
    ) -> FileUploadResponse:
        """Send a file.

        If ``file_id`` is provided, sends via GET (previously uploaded file).
        If ``file`` is provided, uploads via POST (multipart form-data).
        Exactly one of ``file_id`` or ``file`` must be specified.

        Endpoint: GET|POST /messages/sendFile
        """
        _validate_file_source(file_id, file)
        _validate_reply_forward(reply_msg_id, forward_chat_id, forward_msg_id)
        _validate_parse_format(parse_mode, format_)

        if file_id is not None:
            raw = await self._session.get(
                "/messages/sendFile",
                chatId=chat_id,
                fileId=file_id,
                caption=caption,
                replyMsgId=_serialize_msg_ids(reply_msg_id),
                forwardChatId=forward_chat_id,
                forwardMsgId=_serialize_msg_ids(forward_msg_id),
                inlineKeyboardMarkup=_serialize_keyboard(
                    inline_keyboard_markup
                ),
                format=_serialize_format(format_),
                parseMode=parse_mode.value if parse_mode else None,
            )
            return FileUploadResponse.model_validate(raw)

        # file upload (POST)
        form = _build_form_data(file)  # type: ignore[arg-type]
        raw = await self._session.post(
            "/messages/sendFile",
            data=form,
            chatId=chat_id,
            caption=caption,
            replyMsgId=_serialize_msg_ids(reply_msg_id),
            forwardChatId=forward_chat_id,
            forwardMsgId=_serialize_msg_ids(forward_msg_id),
            inlineKeyboardMarkup=_serialize_keyboard(inline_keyboard_markup),
            format=_serialize_format(format_),
            parseMode=parse_mode.value if parse_mode else None,
        )
        return FileUploadResponse.model_validate(raw)

    async def send_voice(
        self,
        chat_id: str,
        *,
        file_id: str | None = None,
        file: str | Path | tuple | None = None,
        reply_msg_id: Any | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: Any | None = None,
        inline_keyboard_markup: Any | None = None,
    ) -> FileUploadResponse:
        """Send a voice message.

        If ``file_id`` is provided, sends via GET.
        If ``file`` is provided, uploads via POST.
        Exactly one must be specified.

        Endpoint: GET|POST /messages/sendVoice
        """
        _validate_file_source(file_id, file)
        _validate_reply_forward(reply_msg_id, forward_chat_id, forward_msg_id)

        if file_id is not None:
            raw = await self._session.get(
                "/messages/sendVoice",
                chatId=chat_id,
                fileId=file_id,
                replyMsgId=_serialize_msg_ids(reply_msg_id),
                forwardChatId=forward_chat_id,
                forwardMsgId=_serialize_msg_ids(forward_msg_id),
                inlineKeyboardMarkup=_serialize_keyboard(
                    inline_keyboard_markup
                ),
            )
            return FileUploadResponse.model_validate(raw)

        form = _build_form_data(file)  # type: ignore[arg-type]
        raw = await self._session.post(
            "/messages/sendVoice",
            data=form,
            chatId=chat_id,
            replyMsgId=_serialize_msg_ids(reply_msg_id),
            forwardChatId=forward_chat_id,
            forwardMsgId=_serialize_msg_ids(forward_msg_id),
            inlineKeyboardMarkup=_serialize_keyboard(inline_keyboard_markup),
        )
        return FileUploadResponse.model_validate(raw)

    async def edit_text(
        self,
        chat_id: str,
        msg_id: str | int,
        text: str,
        *,
        inline_keyboard_markup: Any | None = None,
        format_: Any | None = None,
        parse_mode: ParseMode | None = None,
    ) -> OkResponse:
        """Edit a text message.

        Endpoint: GET /messages/editText
        """
        _validate_parse_format(parse_mode, format_)

        raw = await self._session.get(
            "/messages/editText",
            chatId=chat_id,
            msgId=msg_id,
            text=text,
            inlineKeyboardMarkup=_serialize_keyboard(inline_keyboard_markup),
            format=_serialize_format(format_),
            parseMode=parse_mode.value if parse_mode else None,
        )
        return OkResponse.model_validate(raw)

    async def delete_messages(
        self,
        chat_id: str,
        msg_id: str | int | list,
    ) -> OkResponse:
        """Delete messages.

        Endpoint: GET /messages/deleteMessages
        """
        raw = await self._session.get(
            "/messages/deleteMessages",
            chatId=chat_id,
            msgId=_serialize_msg_ids(msg_id),
        )
        return OkResponse.model_validate(raw)

    async def answer_callback_query(
        self,
        query_id: str,
        *,
        text: str | None = None,
        show_alert: bool | None = None,
        url: str | None = None,
    ) -> OkResponse:
        """Answer a callback query from an inline keyboard button press.

        Endpoint: GET /messages/answerCallbackQuery
        """
        raw = await self._session.get(
            "/messages/answerCallbackQuery",
            queryId=query_id,
            text=text,
            showAlert="true" if show_alert else (
                "false" if show_alert is not None else None
            ),
            url=url,
        )
        return OkResponse.model_validate(raw)

    async def download_file(self, url: str) -> bytes:
        """Download a file from an arbitrary URL.

        Uses a standalone aiohttp session (no base_url) so that
        absolute file URLs returned by the API work correctly.
        """
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=self._session._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()
