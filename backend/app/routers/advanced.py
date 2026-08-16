from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class ExperimentalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str | None = Field(default=None, max_length=80)
    prompt: str = Field(default="", max_length=1000)
    selections: list[str] = Field(default_factory=list, max_length=12)
    metadata: dict[str, str] = Field(default_factory=dict, max_length=12)


def experimental_response(kind: str) -> dict:
    return {
        "status": "experimental-concept-demo",
        "module": kind,
        "syntheticData": True,
        "persistent": False,
        "evaluatedMvp": False,
    }


@router.post("/projects/generate")
async def generate_project(_payload: ExperimentalPayload, _user: Annotated[User, Depends(get_current_user)]) -> dict:
    return experimental_response("human-contribution-projects")


@router.get("/projects")
async def list_projects(_user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    return []


@router.get("/growth")
async def list_growth(_user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    return []


@router.post("/growth")
async def create_growth_event(_payload: ExperimentalPayload, _user: Annotated[User, Depends(get_current_user)]) -> dict:
    return experimental_response("growth-timeline")


@router.get("/learning-paths")
async def list_learning_paths(_user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    return []


@router.post("/learning-paths/recommend")
async def recommend_learning_paths(_payload: ExperimentalPayload, _user: Annotated[User, Depends(get_current_user)]) -> dict:
    return {**experimental_response("learning-paths-prototype"), "recommendations": []}


@router.post("/constitution/generate")
async def generate_constitution(_payload: ExperimentalPayload, _user: Annotated[User, Depends(get_current_user)]) -> dict:
    return experimental_response("personal-ai-constitution")


@router.get("/constitution/me")
async def get_constitution(_user: Annotated[User, Depends(get_current_user)]) -> dict:
    return experimental_response("personal-ai-constitution")


@router.get("/scenarios")
async def list_scenarios(_user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    return []


@router.post("/scenarios/compare")
async def compare_scenarios(_payload: ExperimentalPayload, _user: Annotated[User, Depends(get_current_user)]) -> dict:
    return experimental_response("future-scenarios")
