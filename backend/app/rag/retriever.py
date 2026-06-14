from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import RagSource
from app.config import settings
from app.models import Embedding, Post
from app.rag.embedder import embed_text
from app.rag.indexer import POST_SOURCE_TYPE, build_post_embedding_text
from app.rag.similarity import cosine_similarity_from_distance, is_similarity_strong_enough


@dataclass(frozen=True)
class SimilarProject:
    post_id: int
    title: str
    one_liner: str | None
    similarity: float
    content_text: str

    def to_rag_source(self) -> RagSource:
        summary = self.one_liner or self.content_text[:180]
        return RagSource(
            title=self.title,
            source_id=self.post_id,
            similarity=round(self.similarity, 4),
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
    projects = await retrieve_similar_projects_by_embedding(
        db,
        query_embedding.vector,
        exclude_post_id=post.id,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    return [project.to_rag_source() for project in projects]


async def retrieve_similar_projects_by_embedding(
    db: AsyncSession,
    query_embedding: list[float],
    *,
    exclude_post_id: int | None = None,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> list[SimilarProject]:
    distance = Embedding.embedding.cosine_distance(query_embedding).label("distance")
    stmt = (
        select(Post.id, Post.title, Post.one_liner, Embedding.content_text, distance)
        .join(Embedding, Embedding.source_id == Post.id)
        .where(Embedding.source_type == POST_SOURCE_TYPE)
        .order_by(distance)
        .limit((top_k or settings.rag_top_k) * 2)
    )
    if exclude_post_id is not None:
        stmt = stmt.where(Post.id != exclude_post_id)

    rows = (await db.execute(stmt)).all()
    projects: list[SimilarProject] = []
    for post_id, title, one_liner, content_text, raw_distance in rows:
        similarity = cosine_similarity_from_distance(raw_distance)
        if not is_similarity_strong_enough(similarity, threshold=min_similarity):
            continue
        projects.append(
            SimilarProject(
                post_id=post_id,
                title=title,
                one_liner=one_liner,
                similarity=similarity,
                content_text=content_text,
            )
        )
        if len(projects) >= (top_k or settings.rag_top_k):
            break
    return projects


async def _count_indexed_posts(db: AsyncSession, *, exclude_post_id: int | None) -> int:
    stmt = select(func.count(Embedding.id)).where(Embedding.source_type == POST_SOURCE_TYPE)
    if exclude_post_id is not None:
        stmt = stmt.where(Embedding.source_id != exclude_post_id)
    return int((await db.execute(stmt)).scalar_one())

