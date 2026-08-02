from pydantic import BaseModel


class RoadmapPublic(BaseModel):
    id: str
    created_at: str
    data: dict
