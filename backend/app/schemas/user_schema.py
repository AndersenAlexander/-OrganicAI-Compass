from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    is_demo: bool = False
    email_verified_at: datetime | None = None
    account_status: str = "active"
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
