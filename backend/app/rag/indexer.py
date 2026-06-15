from __future__ import annotations

from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import ProjectAnalysisReport
from app.models import AiReport, Embedding, Post
from app.rag.embedder import embed_text


POST_SOURCE_TYPE = "post"
AI_REPORT_SOURCE_TYPE = "ai_report"


async def index_post_embedding(
    db: AsyncSession,
    post: Post,
    *,
    use_fake: bool | None = None,
) -> Embedding:
    content_text = build_post_embedding_text(post)
    embedding = await embed_text(content_text, use_fake=use_fake)

    await db.execute(
        delete(Embedding).where(
            Embedding.source_type == POST_SOURCE_TYPE,
            Embedding.source_id == post.id,
        )
    )
    row = Embedding(
        source_type=POST_SOURCE_TYPE,
        source_id=post.id,
        embedding=embedding.vector,
        embedding_model=embedding.model,
        dimensions=embedding.dimensions,
        content_text=content_text,
        metadata_={
            "post_id": post.id,
            "title": post.title,
            "post_type": post.post_type,
            "service_url": post.service_url,
            "github_url": post.github_url,
            "tags": [tag.slug for tag in getattr(post, "tags", [])],
            "fake_embedding": embedding.is_fake,
        },
    )
    db.add(row)
    await db.flush()
    return row


async def index_ai_report_embedding(
    db: AsyncSession,
    ai_report: AiReport,
    report: ProjectAnalysisReport,
    *,
    use_fake: bool | None = None,
) -> Embedding:
    content_text = build_report_embedding_text(report)
    embedding = await embed_text(content_text, use_fake=use_fake)

    await db.execute(
        delete(Embedding).where(
            Embedding.source_type == AI_REPORT_SOURCE_TYPE,
            Embedding.source_id == ai_report.id,
        )
    )
    row = Embedding(
        source_type=AI_REPORT_SOURCE_TYPE,
        source_id=ai_report.id,
        embedding=embedding.vector,
        embedding_model=embedding.model,
        dimensions=embedding.dimensions,
        content_text=content_text,
        metadata_={
            "post_id": ai_report.post_id,
            "report_id": ai_report.id,
            "status": report.status.status,
            "fake_embedding": embedding.is_fake,
        },
    )
    db.add(row)
    await db.flush()
    return row


async def backfill_post_embeddings(
    db: AsyncSession,
    posts: list[Post],
    *,
    use_fake: bool | None = None,
) -> list[Embedding]:
    rows: list[Embedding] = []
    for post in posts:
        rows.append(await index_post_embedding(db, post, use_fake=use_fake))
    return rows


def build_post_embedding_text(post: Post) -> str:
    fields: list[str] = [
        _line("project_name", post.title),
        _line("one_liner", post.one_liner),
        _line("body", post.body),
        _line("target_user", post.target_user),
        _line("tech_stack", ", ".join(post.tech_stack or [])),
        _line("tags", ", ".join(tag.slug for tag in getattr(post, "tags", []))),
    ]
    return "\n".join(field for field in fields if field)


def build_report_embedding_text(report: ProjectAnalysisReport) -> str:
    service = report.service_understanding
    diagnosis = report.diagnosis
    fields = [
        _line("service_summary", service.one_line_summary),
        _line("detailed_summary", service.detailed_summary),
        _line("site_structure", service.site_structure_summary),
        _line("service_essence", service.service_essence),
        _line("key_insight", service.key_insight),
        _line("core_features", _join(service.core_features)),
        _line("confirmed_facts", _join(service.confirmed_facts)),
        _line("inferred_facts", _join(service.inferred_facts)),
        _line("strengths", _join(item.title + ": " + item.reason for item in diagnosis.strengths)),
        _line("weaknesses", _join(item.title + ": " + item.reason for item in diagnosis.weaknesses)),
        _line(
            "improvement_plan",
            _join(item.priority + " " + item.action for item in diagnosis.improvement_plan),
        ),
    ]
    return "\n".join(field for field in fields if field)


def _line(label: str, value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return f"[{label}] {text}" if text else ""


def _join(values: Any) -> str:
    return "; ".join(str(value).strip() for value in values if str(value).strip())
