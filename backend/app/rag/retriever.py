from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.schemas import RagSource
from app.config import settings
from app.models import Embedding, Post
from app.rag.embedder import embed_text
from app.rag.indexer import POST_SOURCE_TYPE, build_post_embedding_text
from app.rag.similarity import cosine_similarity_from_distance, is_similarity_strong_enough


RankingMode = Literal["auto", "cosine", "weighted"]
ResolvedRankingMode = Literal["cosine", "weighted"]


@dataclass(frozen=True)
class SimilarProject:
    post_id: int
    title: str
    one_liner: str | None
    similarity: float
    content_text: str
    score: float
    ranking_mode: ResolvedRankingMode
    match_reasons: list[str]
    score_breakdown: dict[str, float] | None

    def to_rag_source(self) -> RagSource:
        summary = self.one_liner or self.content_text[:180]
        return RagSource(
            title=self.title,
            source_id=self.post_id,
            similarity=round(self.score, 4),
            ranking_mode=self.ranking_mode,
            match_reasons=self.match_reasons,
            score_breakdown=(
                {key: round(value, 4) for key, value in self.score_breakdown.items()}
                if self.score_breakdown
                else None
            ),
            summary=summary,
        )


async def retrieve_similar_projects(
    db: AsyncSession,
    post: Post,
    *,
    top_k: int | None = None,
    min_similarity: float | None = None,
    min_indexed_posts: int | None = None,
    use_fake: bool | None = None,
    ranking_mode: RankingMode = "auto",
) -> list[RagSource]:
    total_indexed = await _count_indexed_posts(db, exclude_post_id=post.id)
    required_count = (
        min_indexed_posts
        if min_indexed_posts is not None
        else settings.rag_min_indexed_posts
    )
    if total_indexed < required_count:
        return []

    query_text = build_post_embedding_text(post)
    query_embedding = await embed_text(query_text, use_fake=use_fake)
    resolved_mode = _resolve_ranking_mode(ranking_mode, total_indexed=total_indexed)
    projects = await retrieve_similar_projects_by_embedding(
        db,
        query_embedding.vector,
        query_post=post,
        exclude_post_id=post.id,
        top_k=top_k,
        min_similarity=min_similarity,
        ranking_mode=resolved_mode,
    )
    return [project.to_rag_source() for project in projects]


async def retrieve_similar_projects_by_embedding(
    db: AsyncSession,
    query_embedding: list[float],
    *,
    query_post: Post | None = None,
    exclude_post_id: int | None = None,
    top_k: int | None = None,
    min_similarity: float | None = None,
    ranking_mode: ResolvedRankingMode = "cosine",
) -> list[SimilarProject]:
    distance = Embedding.embedding.cosine_distance(query_embedding).label("distance")
    limit = top_k or settings.rag_top_k
    candidate_limit = limit * (
        settings.rag_weighted_candidate_multiplier if ranking_mode == "weighted" else 2
    )
    stmt = (
        select(Post, Embedding.content_text, distance)
        .join(Embedding, Embedding.source_id == Post.id)
        .options(selectinload(Post.tags))
        .where(Embedding.source_type == POST_SOURCE_TYPE)
        .order_by(distance)
        .limit(candidate_limit)
    )
    if exclude_post_id is not None:
        stmt = stmt.where(Post.id != exclude_post_id)

    rows = (await db.execute(stmt)).all()
    projects: list[SimilarProject] = []
    for candidate_post, content_text, raw_distance in rows:
        similarity = cosine_similarity_from_distance(raw_distance)
        if not is_similarity_strong_enough(similarity, threshold=min_similarity):
            continue
        score_breakdown = _score_breakdown(
            similarity,
            query_post=query_post,
            candidate_post=candidate_post,
        )
        score = (
            _weighted_score(score_breakdown)
            if ranking_mode == "weighted" and query_post is not None
            else similarity
        )
        projects.append(
            SimilarProject(
                post_id=candidate_post.id,
                title=candidate_post.title,
                one_liner=candidate_post.one_liner,
                similarity=similarity,
                content_text=content_text,
                score=score,
                ranking_mode=ranking_mode,
                match_reasons=_match_reasons(
                    query_post=query_post,
                    candidate_post=candidate_post,
                    semantic_similarity=similarity,
                    score_breakdown=score_breakdown,
                ),
                score_breakdown=score_breakdown if ranking_mode == "weighted" else None,
            )
        )
        if ranking_mode == "cosine" and len(projects) >= limit:
            break
    if ranking_mode == "weighted":
        projects.sort(key=lambda item: item.score, reverse=True)
    return projects[:limit]


async def _count_indexed_posts(db: AsyncSession, *, exclude_post_id: int | None) -> int:
    stmt = select(func.count(Embedding.id)).where(Embedding.source_type == POST_SOURCE_TYPE)
    if exclude_post_id is not None:
        stmt = stmt.where(Embedding.source_id != exclude_post_id)
    return int((await db.execute(stmt)).scalar_one())


def _resolve_ranking_mode(
    ranking_mode: RankingMode,
    *,
    total_indexed: int,
) -> ResolvedRankingMode:
    if ranking_mode == "weighted":
        return "weighted"
    if ranking_mode == "cosine":
        return "cosine"
    if total_indexed >= settings.rag_weighted_min_indexed_posts:
        return "weighted"
    return "cosine"


def _score_breakdown(
    semantic_similarity: float,
    *,
    query_post: Post | None,
    candidate_post: Post,
) -> dict[str, float]:
    return {
        "semantic": semantic_similarity,
        "tag_overlap": _tag_overlap_score(query_post, candidate_post),
        "vote": _vote_score(candidate_post.score),
        "recency": _recency_score(candidate_post.created_at),
        "same_type": _same_type_score(query_post, candidate_post),
    }


def _weighted_score(score_breakdown: dict[str, float]) -> float:
    return (
        score_breakdown["semantic"] * 0.65
        + score_breakdown["tag_overlap"] * 0.15
        + score_breakdown["vote"] * 0.10
        + score_breakdown["recency"] * 0.05
        + score_breakdown["same_type"] * 0.05
    )


def _tag_overlap_score(query_post: Post | None, candidate_post: Post) -> float:
    if query_post is None:
        return 0.0
    query_tags = {tag.slug for tag in getattr(query_post, "tags", [])}
    candidate_tags = {tag.slug for tag in getattr(candidate_post, "tags", [])}
    union = query_tags | candidate_tags
    if not union:
        return 0.0
    return len(query_tags & candidate_tags) / len(union)


def _vote_score(score: int | None) -> float:
    if score is None or score <= 0:
        return 0.0
    return min(1.0, float(score) / 10.0)


def _recency_score(created_at: datetime | None) -> float:
    if created_at is None:
        return 0.0
    value = created_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    age_days = max(0, (datetime.now(timezone.utc) - value).days)
    return max(0.0, 1.0 - (age_days / 90.0))


def _same_type_score(query_post: Post | None, candidate_post: Post) -> float:
    if query_post is None:
        return 0.0
    return 1.0 if query_post.post_type == candidate_post.post_type else 0.0


def _match_reasons(
    *,
    query_post: Post | None,
    candidate_post: Post,
    semantic_similarity: float,
    score_breakdown: dict[str, float],
) -> list[str]:
    reasons = [f"본문/요약 임베딩 유사도 {round(semantic_similarity * 100)}%"]
    if query_post is None:
        return reasons

    query_tags = {tag.slug for tag in getattr(query_post, "tags", [])}
    candidate_tags = {tag.slug for tag in getattr(candidate_post, "tags", [])}
    shared_tags = sorted(query_tags & candidate_tags)
    if shared_tags:
        reasons.append("겹치는 태그: " + ", ".join(shared_tags[:3]))
    if score_breakdown["same_type"] > 0:
        reasons.append("같은 게시물 유형")
    if score_breakdown["vote"] > 0:
        reasons.append("게시판 반응 점수 반영")
    if score_breakdown["recency"] >= 0.8:
        reasons.append("최근 등록된 프로젝트")
    return reasons[:4]
