from pydantic import BaseModel, ConfigDict


class VKTeamsModel(BaseModel):
    """Strict base model for response types where schemas are stable.

    Uses extra="forbid" to catch schema drift immediately.
    """

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="forbid",
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
