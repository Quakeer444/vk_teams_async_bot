from pydantic import BaseModel, ConfigDict


class VKTeamsModel(BaseModel):
    """Strict base model for internal types where schemas are stable.

    Uses extra="forbid" to catch schema drift immediately.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="forbid",
    )


class VKTeamsResponseModel(BaseModel):
    """Base model for API response types.

    Uses extra="ignore" so new fields from VK Teams API
    do not crash existing users.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="ignore",
    )


class VKTeamsFlexModel(BaseModel):
    """Permissive base model for event/message models.

    Uses extra="allow" because VK Teams may add fields without notice.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="allow",
    )
