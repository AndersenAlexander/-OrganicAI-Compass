from pydantic import BaseModel


class ProfilePublic(BaseModel):
    id: str
    created_at: str
    data: dict
