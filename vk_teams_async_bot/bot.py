import asyncio
import logging
from io import BytesIO
from typing import TypeAlias

import aiohttp
from aiohttp import FormData

from .client_session import VKTeamsSession
from .constants import ParseMode
from .dispatcher import Dispatcher
from .events import Event, EventType
from .helpers import Format, InlineKeyboardMarkup, async_read_file, format_to_json
from .state import DictUserState

logger = logging.getLogger(__name__)

Seconds: TypeAlias = int


class EventsKeyMissingError(Exception):
    pass


class Bot(object):
    """
    Basic description Bot API - https://teams.vk.com/botapi/
    """

    def __init__(
        self,
        bot_token: str,
        url: str = "https://api.internal.myteam.mail.ru",
        base_path="/bot/v1/",
        timeout_session: Seconds = 30,
        poll_time: Seconds = 15,
        last_event_id: int = 0,
    ):
        """

        :param bot_token: Bot token
        :param url: Server Bot API
        :param base_path: Base path
        :param timeout_session: Timeout aiohttp session
        :param poll_time: Time polling /events/get
        :param last_event_id: Last event count
        """
        self.timeout_session = timeout_session
        self.bot_token = bot_token
        self.last_event_id = last_event_id
        self.poll_time = poll_time

        self.session = VKTeamsSession(url, base_path, bot_token, timeout_session)

        self.dispatcher = Dispatcher(self)
        self.user_state = DictUserState(self.send_text)
        self.depends: list = []

    async def start_polling(self, count_request_retries: int = 2) -> None:
        """
        Basic method to start polling

        :param count_request_retries: number of request retries in case of
               500+ code response from server VK Teams
        """
        while True:
            try:
                events = await self.get_events(count_request_retries)
                if events:
                    for event in events:
                        event = Event(
                            type_=EventType(event["type"]), data=event["payload"]
                        )
                        asyncio.create_task(self.dispatcher.processed_event(event))

            except Exception as err:
                logger.error(err, exc_info=True)

    async def get_events(self, count_request_retries: int) -> list | None:
        """
        Get events from VK Teams API

        :param count_request_retries: number of request retries in case of
               500+ code response from server VK Teams

        :return: list of one or several events
        """
        response: dict = await self.session.get_request(
            endpoint="events/get",
            lastEventId=self.last_event_id,
            pollTime=self.poll_time,
            _count_request_retries=count_request_retries,
        )
        if response:
            try:
                if not response.__contains__("events"):
                    raise EventsKeyMissingError

                if response.get("events"):
                    self.set_last_event_id(response["events"][-1]["eventId"])
                    return response["events"]

            except EventsKeyMissingError:
                logger.error(f"Key events not found - {response=}")
        return None

    def set_last_event_id(self, event_id: int) -> None:
        """
        Incrementing the last event counter

        :param event_id: last event id
        """
        self.last_event_id = event_id

    async def answer_callback_query(
        self,
        query_id: str,
        text: str = "",
        show_alert: bool = False,
        url: str | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """
        Calling this method must be used in response to receiving the [callbackQuery] event

        :param query_id: ID of the callback query received by the bot
        :param text: Notification text that will be displayed to the user.
                      If the text is not specified, nothing will be displayed.

        :param show_alert: If set to true, an alert will be shown instead of a notification
        :param url: URL that will be opened by the client application
        :param count_request_retries:
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}

        """
        return await self.session.get_request(
            endpoint="messages/answerCallbackQuery",
            queryId=query_id,
            text=text,
            showAlert="true" if show_alert else "false",
            url=url,
            _count_request_retries=count_request_retries,
        )

    async def get_file_info(self, file_id: str) -> dict:
        """
        Get file information from VK Teams API

        :param file_id: ID of a previously uploaded file on the server

        :return: Response 200
        {
              "type": "video",
              "size": 20971520,
              "filename": "VIDEO.mkv",
              "url": "https://example.com/get/88MfCLBHphvOAOeuzYhZfW5b7bcfa31ab"
        }
        """
        response = await self.session.get_request(
            endpoint="files/getInfo", fileId=file_id, _count_request_retries=2
        )
        return response

    async def send_text(
        self,
        chat_id: str,
        text: str,
        reply_msg_id: list[str] | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: str | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """
        Send a text message

        :param chat_id: Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param text: Text message. You can mention a user by adding
               their userId to the text in the following format @[userId].
        :param reply_msg_id: ID of the quoted message. Cannot be passed
               simultaneously with forwardChatId and forwardMsgId parameters.
        :param forward_chat_id: Id of the chat from which the message will be forwarded.
               Sent only with forwardMsgId. Cannot be passed with the replyMsgId parameter.
        :param forward_msg_id: ID of the message being forwarded.
               Sent only with forwardChatId. Cannot be passed with the replyMsgId parameter.
        :param inline_keyboard_markup: This is an array of arrays with button descriptions.
               The top level is an array of button strings, the lower level is an array
               of buttons in a specific line
        :param _format: Description of text formatting.
        :param parse_mode: Mode for processing formatting from message text.
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """

        return await self.session.get_request(
            endpoint="messages/sendText",
            chatId=chat_id,
            text=text,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inlineKeyboardMarkup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parseMode=parse_mode,
            _count_request_retries=count_request_retries,
        )

    async def send_file_by_id(
        self,
        chat_id: str,
        file_id: str,
        caption: str | None = None,
        reply_msg_id: list[int] | None = None,
        forward_chat_id: list[str] | None = None,
        forward_msg_id: list[int] | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        return await self.session.get_request(
            endpoint="messages/sendFile",
            chatId=chat_id,
            fileId=file_id,
            caption=caption,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inlineKeyboardMarkup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parseMode=parse_mode,
            _count_request_retries=count_request_retries,
        )

    async def edit_text(
        self,
        chat_id: str,
        msg_id: int,
        text: str,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """

        :param chat_id: Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param msg_id: Message ID
        :param text: Text message. You can mention a user by adding
               their userId to the text in the following format @[userId].
        :param inline_keyboard_markup: This is an array of arrays with button descriptions.
               The top level is an array of button strings, the lower level is an array
               of buttons in a specific line
        :param _format: Description of text formatting.
        :param parse_mode: Mode for processing formatting from message text.
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """

        return await self.session.get_request(
            endpoint="messages/editText",
            chatId=chat_id,
            msgId=msg_id,
            text=text,
            inlineKeyboardMarkup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parseMode=parse_mode,
            _count_request_retries=count_request_retries,
        )

    async def send_file(
        self,
        chat_id: str,
        bytes_io_object: BytesIO | None = None,
        file_path: str | None = None,
        filename: str | None = None,
        caption: str | None = None,
        reply_msg_id: list[int] | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: list[int] | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """
        Method for sending a message with a file. The file is read from the path
        if file_path is specified, in case of passing a BytesIO object, specify
        only the bytes_object parameter

        :param chat_id: Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param bytes_io_object:
        :param file_path: File path
        :param filename: Filename with extension
        :param caption: File signature
        :param reply_msg_id: ID of the quoted message. Cannot be passed
               simultaneously with forwardChatId and forwardMsgId parameters.
        :param forward_chat_id: Id of the chat from which the message will be forwarded.
               Sent only with forwardMsgId. Cannot be passed with the replyMsgId parameter.
        :param forward_msg_id: ID of the message being forwarded.
               Sent only with forwardChatId. Cannot be passed with the replyMsgId parameter.
        :param inline_keyboard_markup: This is an array of arrays with button descriptions.
               The top level is an array of button strings, the lower level is an array
               of buttons in a specific line
        :param _format: Description of text formatting.
        :param parse_mode: Mode for processing formatting from message text.
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """
        data = FormData()

        if file_path:
            data.add_field("file", await async_read_file(file_path), filename=filename)
        if bytes_io_object:
            data.add_field(
                "file",
                bytes_io_object,
                filename=filename,
                content_type="application/octet-stream",
            )

        return await self.session.post_request(
            endpoint="messages/sendFile",
            chatId=chat_id,
            body=data,
            caption=caption,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inline_keyboard_markup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parse_mode=parse_mode,
            _count_request_retries=count_request_retries,
        )

    @staticmethod
    async def download_file(file_url: str) -> bytes:
        """
        Method for downloading a file

        :param file_url: The URL of the file to download.
        :return: - bytes: The content of the file as bytes
                 - None: If the response status code is not 200.
        """
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    return await response.read()

    async def delete_msg(
        self, chat_id: str, msg_id: list[str], count_request_retries: int = 2
    ):
        """
        Delete a message

        :param chat_id: Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param msg_id: Message ID
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """
        return await self.session.get_request(
            endpoint="messages/deleteMessages",
            chatId=chat_id,
            msgId=msg_id,
            _count_request_retries=count_request_retries,
        )

    async def self_get(self, count_request_retries: int = 2) -> dict:
        """
        Method for checking the validity of a token

        :return: Response 200 {"ok": true}

        {
              "userId": "747432131",
              "nick": "test_api_bot",
              "firstName": "TestBot",
              "about": "The description of the bot",
              "photo": [
                {
                  "url": "https://example.com/expressions/getAsset..."
                }
              ],
              "ok": true
        }
        """
        return await self.session.get_request(
            "self/get", _count_request_retries=count_request_retries
        )

    async def send_voice(
        self,
        chat_id: str,
        file_path: str,
        filename: str,
        reply_msg_id: list[int] | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: list[int] | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """
        Send voice messages

        :param chat_id:Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param file_path: File path
        :param filename: Filename with extension
        :param reply_msg_id: ID of the quoted message. Cannot be passed
               simultaneously with forwardChatId and forwardMsgId parameters.
        :param forward_chat_id: Id of the chat from which the message will be forwarded.
               Sent only with forwardMsgId. Cannot be passed with the replyMsgId parameter.
        :param forward_msg_id: ID of the message being forwarded.
               Sent only with forwardChatId. Cannot be passed with the replyMsgId parameter.
        :param inline_keyboard_markup: This is an array of arrays with button descriptions.
               The top level is an array of button strings, the lower level is an array
               of buttons in a specific line
        :param _format: Description of text formatting.
        :param parse_mode: Mode for processing formatting from message text.
        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """

        data = FormData()
        data.add_field("file", await async_read_file(file_path), filename=filename)

        return await self.session.post_request(
            endpoint="messages/sendVoice",
            chatId=chat_id,
            body=data,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inline_keyboard_markup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parseMode=parse_mode,
            _count_request_retries=count_request_retries,
        )

    async def send_voice_by_id(
        self,
        chat_id: str,
        file_id: str,
        reply_msg_id: list[int] | None = None,
        forward_chat_id: list[str] | None = None,
        forward_msg_id: list[int] | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        count_request_retries: int = 2,
    ) -> dict:
        """
        Send voice messages by ID file from server.
        If you want the client to display this file as a playable voice message,
        it must be in aac, ogg, or m4a format.

        :param chat_id: Unique nickname or chat id.
               Id can be obtained from incoming events (chatId field).
        :param file_id: File ID
        :param reply_msg_id: ID of the quoted message. Cannot be passed
               simultaneously with forwardChatId and forwardMsgId parameters.
        :param forward_chat_id: Id of the chat from which the message will be forwarded.
               Sent only with forwardMsgId. Cannot be passed with the replyMsgId parameter.
        :param forward_msg_id: ID of the message being forwarded.
               Sent only with forwardChatId. Cannot be passed with the replyMsgId parameter.
        :param inline_keyboard_markup: This is an array of arrays with button descriptions.
               The top level is an array of button strings, the lower level is an array
               of buttons in a specific line

        :param count_request_retries: number of request retries in case of
               500 response from server VK Teams

        :return: Response 200 {"ok": true}
        """

        return await self.session.get_request(
            endpoint="messages/sendVoice",
            chatId=chat_id,
            fileId=file_id,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inlineKeyboardMarkup=str(inline_keyboard_markup)
            if inline_keyboard_markup is not None
            else None,
            _count_request_retries=count_request_retries,
        )
