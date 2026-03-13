import json

from vk_teams_async_bot.types.enums import StyleType
from vk_teams_async_bot.types.format_ import Format, Style


class TestStyle:
    def test_add_range(self):
        s = Style()
        s.add(0, 5)
        assert s.to_list() == [{"offset": 0, "length": 5}]

    def test_add_range_with_kwargs(self):
        s = Style()
        s.add(0, 10, url="https://example.com")
        result = s.to_list()
        assert result == [{"offset": 0, "length": 10, "url": "https://example.com"}]

    def test_multiple_ranges(self):
        s = Style()
        s.add(0, 5)
        s.add(10, 3)
        assert len(s.to_list()) == 2

    def test_to_json(self):
        s = Style()
        s.add(0, 5)
        parsed = json.loads(s.to_json())
        assert parsed == [{"offset": 0, "length": 5}]


class TestFormat:
    def test_add_style(self):
        f = Format()
        f.add(StyleType.BOLD, 0, 5)
        result = f.to_dict()
        assert "bold" in result
        assert result["bold"] == [{"offset": 0, "length": 5}]

    def test_multiple_styles(self):
        f = Format()
        f.add(StyleType.BOLD, 0, 5)
        f.add(StyleType.ITALIC, 6, 3)
        result = f.to_dict()
        assert "bold" in result
        assert "italic" in result

    def test_same_style_multiple_ranges(self):
        f = Format()
        f.add(StyleType.BOLD, 0, 5)
        f.add(StyleType.BOLD, 10, 3)
        result = f.to_dict()
        assert len(result["bold"]) == 2

    def test_link_with_url(self):
        f = Format()
        f.add(StyleType.LINK, 0, 10, url="https://example.com")
        result = f.to_dict()
        assert result["link"][0]["url"] == "https://example.com"

    def test_to_json(self):
        f = Format()
        f.add(StyleType.BOLD, 0, 5)
        parsed = json.loads(f.to_json())
        assert parsed == {"bold": [{"offset": 0, "length": 5}]}

    def test_chaining(self):
        f = Format().add(StyleType.BOLD, 0, 5).add(StyleType.ITALIC, 6, 3)
        result = f.to_dict()
        assert "bold" in result
        assert "italic" in result
