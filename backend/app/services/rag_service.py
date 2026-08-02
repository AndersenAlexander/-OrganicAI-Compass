from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

from app.config import get_settings
from app.services.embedding_service import embed_text, embed_texts
from app.services.knowledge_loader import load_knowledge_chunks


@dataclass(frozen=True)
class RagSource:
    id: str
    document_name: str
    section_title: str
    chunk_text: str
    score: float


def vector_store_path() -> Path:
    path = Path(__file__).resolve().parents[1] / "media" / "rag" / "vector_store.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    length = min(len(a), len(b))
    if length == 0:
        return 0.0
    dot = sum(a[index] * b[index] for index in range(length))
    norm_a = math.sqrt(sum(value * value for value in a[:length])) or 1.0
    norm_b = math.sqrt(sum(value * value for value in b[:length])) or 1.0
    return dot / (norm_a * norm_b)


def _load_store() -> list[dict[str, object]]:
    path = vector_store_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_store(records: list[dict[str, object]]) -> None:
    vector_store_path().write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


async def reindex_knowledge_base() -> dict[str, int]:
    chunks = load_knowledge_chunks()
    embeddings = await embed_texts([chunk.chunk_text for chunk in chunks]) if chunks else []
    records = []
    for chunk, embedding in zip(chunks, embeddings):
        records.append({**asdict(chunk), "embedding": embedding})
    _save_store(records)
    return {"documents": len({chunk.document_name for chunk in chunks}), "chunks": len(records)}


async def search_knowledge_base(query: str, top_k: int | None = None) -> list[RagSource]:
    settings = get_settings()
    records = _load_store()
    if not records:
        await reindex_knowledge_base()
        records = _load_store()

    if not records:
        return []

    query_embedding = await embed_text(query)
    ranked: list[RagSource] = []
    for record in records:
        embedding = record.get("embedding")
        if not isinstance(embedding, list):
            continue
        score = _cosine_similarity(query_embedding, [float(value) for value in embedding])
        ranked.append(
            RagSource(
                id=str(record["id"]),
                document_name=str(record["document_name"]),
                section_title=str(record["section_title"]),
                chunk_text=str(record["chunk_text"]),
                score=score,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    limit = top_k or settings.rag_top_k
    return ranked[:limit]


async def ask_with_rag(query: str) -> dict[str, object]:
    sources = await search_knowledge_base(query)
    relevant_sources = [source for source in sources if source.score > 0.05]
    return {
        "query": query,
        "sources": [asdict(source) for source in relevant_sources],
        "has_sources": bool(relevant_sources),
    }


def format_sources_for_prompt(sources: list[RagSource]) -> str:
    if not sources:
        return "No OrganicAI Knowledge Base sources were relevant for this query."

    lines = []
    for index, source in enumerate(sources, start=1):
        lines.append(
            f"[Source {index}: {source.document_name} / {source.section_title}]\n{source.chunk_text}"
        )
    return "\n\n".join(lines)
