from __future__ import annotations

import hashlib
import math

from openai import AsyncOpenAI

from app.config import get_settings, resolve_active_openai_api_key


def _hash_embedding(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    tokens = [token.strip(".,:;!?()[]{}\"'").lower() for token in text.split()]
    for token in tokens:
        if not token:
            continue
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    api_key = resolve_active_openai_api_key(settings)
    if not api_key:
        return [_hash_embedding(text) for text in texts]

    client = AsyncOpenAI(api_key=api_key, timeout=20.0, max_retries=1)
    response = await client.embeddings.create(model=settings.openai_embedding_model, input=texts)
    return [item.embedding for item in response.data]


async def embed_text(text: str) -> list[float]:
    return (await embed_texts([text]))[0]
