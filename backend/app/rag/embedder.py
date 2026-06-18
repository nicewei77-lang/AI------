from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings


EMBEDDING_DIMENSIONS = 1536
TOKEN_RE = re.compile(r"[\w가-힣]+", flags=re.UNICODE)


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model: str
    dimensions: int
    is_fake: bool


async def embed_text(
    text: str,
    *,
    model: str | None = None,
    use_fake: bool | None = None,
) -> EmbeddingResult:
    model_name = model or settings.embedding_model
    should_fake = use_fake if use_fake is not None else not bool(settings.openai_api_key)
    bounded_text = _prepare_text(text)

    if should_fake:
        return EmbeddingResult(
            vector=fake_embedding(bounded_text),
            model=f"fake:{model_name}",
            dimensions=EMBEDDING_DIMENSIONS,
            is_fake=True,
        )

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_request_timeout_seconds,
        max_retries=1,
    )
    response = await client.embeddings.create(model=model_name, input=bounded_text)
    vector = list(response.data[0].embedding)
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding dimensions mismatch: expected {EMBEDDING_DIMENSIONS}, got {len(vector)}"
        )
    return EmbeddingResult(
        vector=vector,
        model=model_name,
        dimensions=len(vector),
        is_fake=False,
    )


def fake_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = TOKEN_RE.findall(text.lower()) or ["empty"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _prepare_text(text: str) -> str:
    stripped = re.sub(r"\s+", " ", text).strip()
    if not stripped:
        return "empty ProjectLens source"
    return stripped[:12_000]
