from .base import VKTeamsModel


class FileInfo(VKTeamsModel):
    type: str
    size: int
    filename: str
    url: str
