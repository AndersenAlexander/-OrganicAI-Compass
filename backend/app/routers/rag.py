from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.rag_service import ask_with_rag, reindex_knowledge_base, search_knowledge_base

router = APIRouter()


class RagAskRequest(BaseModel):
    query: str


@router.post("/reindex")
async def reindex() -> dict[str, int]:
    return await reindex_knowledge_base()


@router.get("/search")
async def search(query: str = Query(..., min_length=2)) -> dict[str, object]:
    sources = await search_knowledge_base(query)
    return {"query": query, "results": [source.__dict__ for source in sources]}


@router.post("/ask")
async def ask(request: RagAskRequest) -> dict[str, object]:
    return await ask_with_rag(request.query)
