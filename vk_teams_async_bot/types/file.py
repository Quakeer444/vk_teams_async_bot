from .base import VKTeamsResponseModel


class FileInfo(VKTeamsResponseModel):
    type: str
    size: int
    filename: str
    url: str
