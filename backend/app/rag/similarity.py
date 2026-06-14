from __future__ import annotations

from app.config import settings


def cosine_similarity_from_distance(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - float(distance)))


def is_similarity_strong_enough(
    similarity: float,
    *,
    threshold: float | None = None,
) -> bool:
    return similarity >= (threshold if threshold is not None else settings.rag_similarity_threshold)

