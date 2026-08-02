from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    is_demo: bool = False
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
