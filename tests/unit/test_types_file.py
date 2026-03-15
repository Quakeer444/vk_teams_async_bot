import pytest
from pydantic import ValidationError

from vk_teams_async_bot.types.file import FileInfo


class TestFileInfo:
    def test_from_dict(self):
        data = {
            "type": "image",
            "size": 1024,
            "filename": "photo.jpg",
            "url": "https://files.example.com/photo.jpg",
        }
        f = FileInfo(**data)
        assert f.type == "image"
        assert f.size == 1024
        assert f.filename == "photo.jpg"
        assert f.url == "https://files.example.com/photo.jpg"

    def test_round_trip(self):
        data = {"type": "audio", "size": 2048, "filename": "song.mp3", "url": "https://x.com/song.mp3"}
        f = FileInfo(**data)
        assert f.model_dump() == data

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            FileInfo(type="image", size=100, filename="x.jpg")

    def test_extra_ignored(self):
        f = FileInfo(type="image", size=100, filename="x.jpg", url="u", extra="no")
        assert f.type == "image"
