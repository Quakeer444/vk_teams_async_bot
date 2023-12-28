import asyncio
import logging
from typing import TypeAlias

from aiohttp import FormData

from .client_session import VKTeamsSession
from .constants import ParseMode
from .dispatcher import Dispatcher
from .events import Event, EventType
from .helpers import (Format, InlineKeyboardMarkup, async_read_file,
                      format_to_json)
from .state import DictUserState

logger = logging.getLogger(__name__)

Seconds: TypeAlias = int


class EventsKeyMissingError(Exception):
    pass


class Bot(object):
    """
    Основное описание Bot API - https://teams.vk.com/botapi/
    """

    def __init__(
        self,
        bot_token: str,
        url: str = "https://api.internal.myteam.mail.ru",
        base_path="/bot/v1/",
        timeout_session: Seconds = 35,
        poll_time: Seconds = 20,
        last_event_id: int = 0,
    ):
        """

        :param bot_token: Токен бота
        :param url: Сервер Bot API
        :param base_path: Базовый путь
        :param timeout_session: Таймаут aiohttp сессии
        :param poll_time: Время поллига /events/get
        :param last_event_id: Счётчик последнего события
        """
        self.timeout_session = timeout_session
        self.bot_token = bot_token

        self.last_event_id = last_event_id
        self.poll_time = poll_time
        self.session = VKTeamsSession(url, base_path, bot_token, timeout_session)
        self.dispatcher = Dispatcher(self)
        self.user_state = DictUserState(self.send_text)
        self.depends = []

    async def start_polling(self) -> None:
        """
        Основной метод для обработки событий
        """
        while True:
            try:
                events: list = await self.get_events()
                if events:
                    for event in events:
                        event = Event(
                            type_=EventType(event["type"]), data=event["payload"]
                        )
                        asyncio.create_task(self.dispatcher.processed_event(event))

            except Exception as err:
                logger.error(err, exc_info=True)

    async def get_events(self) -> list:
        """
        Поллинг событий от Bot API
        :return: Список одного или нескольких событий
        """
        response: dict = await self.session.get_request(
            endpoint="events/get",
            lastEventId=self.last_event_id,
            pollTime=self.poll_time,
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

    def set_last_event_id(self, event_id: int) -> None:
        """
        Увеличение счётчика последнего события
        """
        self.last_event_id = event_id

    async def answer_callback_query(
        self,
        query_id: str,
        text: str = "",
        show_alert: bool = False,
        url: str = None,
    ) -> dict:
        """
        Вызов данного метода должен использоваться в ответ на получение события [callbackQuery]
        :param query_id: Идентификатор callback query полученного ботом
        :param text: Текст нотификации, который будет отображен пользователю.
                     В случае, если текст не задан – ничего не будет отображено.

        :param show_alert: Если выставить значение в true, вместо нотификации будет показан
        :param url: URL, который будет открыт клиентским приложением
        :return: Response 200 {"ok": true}

        """
        return await self.session.get_request(
            endpoint="messages/answerCallbackQuery",
            queryId=query_id,
            text=text,
            showAlert="true" if show_alert else "false",
            url=url,
        )

    async def get_file_info(self, file_id: str) -> dict:
        """
        Получение информации о файле на сервере
        :param file_id: Id ранее загруженного файла на сервере
        :return: Response 200
        {
              "type": "video",
              "size": 20971520,
              "filename": "VIDEO.mkv",
              "url": "https://example.com/get/88MfCLBHphvOAOeuzYhZfW5b7bcfa31ab"
        }
        """
        response = await self.session.get_request(
            endpoint="files/getInfo", fileId=file_id
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
    ) -> dict:
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
        )

    async def send_file_id(
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
        )

    async def edit_text(
        self,
        chat_id: str,
        msg_id: int,
        text: str,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
    ) -> dict:
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
        )

    async def send_file(
        self,
        chat_id: str,
        file_path: str,
        filename: str = None,
        caption: str | None = None,
        reply_msg_id: list[int] | None = None,
        forward_chat_id: str | None = None,
        forward_msg_id: list[int] | None = None,
        inline_keyboard_markup: InlineKeyboardMarkup | str | None = None,
        _format: Format | list[dict] | str | None = None,
        parse_mode: ParseMode | None = None,
    ) -> dict:
        """
        Метод для отправки сообщения с файлом по его file.
        """
        data = FormData()
        data.add_field("file", await async_read_file(file_path), filename=filename)

        return await self.session.post_request(
            endpoint="messages/sendFile",
            chatId=chat_id,
            body=data,
            caption=caption,
            replyMsgId=reply_msg_id,
            forwardChatId=forward_chat_id,
            forwardMsgId=forward_msg_id,
            inline_keyboard_markup=str(inline_keyboard_markup),
            format=_format if isinstance(_format, str) else format_to_json(_format),
            parse_mode=parse_mode,
        )

    async def delete_msg(self, chat_id: str, msg_id: list[str]):
        return await self.session.get_request(
            endpoint="messages/deleteMessages", chatId=chat_id, msgId=msg_id
        )

    async def self_get(self) -> dict:
        """
        Метод можно использовать для проверки валидности токена.
        :return: Response 200

        {
              "userId": "747432131",
              "nick": "test_api_bot",
              "firstName": "TestBot",
              "about": "The description of the bot",
              "photo": [
                {
                  "url": "https://example.com/expressions/getAsset?f=native&type=largeBuddyIcon&id=01103"
                }
              ],
              "ok": true
        }
        """
        return await self.session.get_request("self/get")
