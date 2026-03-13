from vk_teams_async_bot.types.enums import (
    ChatAction,
    ChatType,
    EventType,
    ParseMode,
    Parts,
    StyleKeyboard,
    StyleType,
)


class TestEnums:
    def test_parse_mode_values(self):
        assert ParseMode.MARKDOWNV2 == "MarkdownV2"
        assert ParseMode.HTML == "HTML"

    def test_chat_type_values(self):
        assert ChatType.PRIVATE == "private"
        assert ChatType.GROUP == "group"
        assert ChatType.CHANNEL == "channel"

    def test_style_keyboard_values(self):
        assert StyleKeyboard.BASE == "base"
        assert StyleKeyboard.PRIMARY == "primary"
        assert StyleKeyboard.ATTENTION == "attention"

    def test_parts_values(self):
        assert Parts.FILE == "file"
        assert Parts.STICKER == "sticker"
        assert Parts.MENTION == "mention"
        assert Parts.VOICE == "voice"
        assert Parts.FORWARD == "forward"
        assert Parts.REPLY == "reply"

    def test_style_type_values(self):
        assert StyleType.BOLD == "bold"
        assert StyleType.LINK == "link"
        assert StyleType.PRE == "pre"
        assert len(StyleType) == 11

    def test_chat_action_values(self):
        assert ChatAction.TYPING == "typing"
        assert ChatAction.LOOKING == "looking"

    def test_event_type_values(self):
        assert EventType.NEW_MESSAGE == "newMessage"
        assert EventType.CALLBACK_QUERY == "callbackQuery"
        assert len(EventType) == 8

    def test_strenum_string_comparison(self):
        assert ParseMode.HTML == "HTML"
        assert ChatType.PRIVATE == "private"
        assert EventType.NEW_MESSAGE == "newMessage"
