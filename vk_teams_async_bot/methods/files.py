"""File-related API methods."""

from __future__ import annotations

from vk_teams_async_bot.types.file import FileInfo

from .base import BaseMethods


class FileMethods(BaseMethods):
    """Mixin providing /files/* API methods."""

    async def get_file_info(self, file_id: str) -> FileInfo:
        """Get file information.

        Endpoint: GET /files/getInfo
        """
        raw = await self._session.get(
            "/files/getInfo",
            fileId=file_id,
        )
        return FileInfo.model_validate(raw)
