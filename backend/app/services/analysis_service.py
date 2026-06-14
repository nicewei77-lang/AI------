from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.context import AnalysisToolContext, CollectedMcpEvidence
from app.ai.runner import (
    ProjectAnalysisRun,
    build_failed_report,
    build_need_more_info_report,
    build_runner_input,
    run_project_analysis,
)
from app.ai.schemas import ProjectAnalysisReport, ReportStatus
from app.config import settings
from app.mcp_client.client import record_mcp_evidence
from app.models import AiReport, Post
from app.rag.indexer import index_ai_report_embedding, index_post_embedding
from app.rag.retriever import retrieve_similar_projects


class AnalysisPostNotFoundError(LookupError):
    pass


class AnalysisReportNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class PersistedAnalysis:
    status: ReportStatus
    report_id: int
    report: ProjectAnalysisReport
    model: str | None
    reasoning_effort: str | None
    response_id: str | None
    trace_id: str | None
    usage: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: datetime | None = None


async def run_analysis_for_post(db: AsyncSession, post_id: int) -> PersistedAnalysis:
    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    post.analysis_status = "running"
    await db.commit()

    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    missing_fields, questions = _missing_required_fields(post)
    if missing_fields:
        report = build_need_more_info_report(missing_fields, questions)
        run = ProjectAnalysisRun(
            report=report,
            model=settings.agent_model,
            reasoning_effort=settings.reasoning_effort,
            response_id=None,
            trace_id=None,
            usage=None,
            error=None,
        )
        return await _persist_analysis(db, post, run, [])

    tool_context = AnalysisToolContext(
        post_id=post.id,
        service_url=post.service_url,
        github_url=post.github_url,
    )
    rag_sources = []
    try:
        await index_post_embedding(db, post)
        rag_sources = await retrieve_similar_projects(db, post)
        input_payload = build_runner_input(
            post=_post_snapshot(post),
            mcp_evidence=tool_context.mcp_evidence,
            rag_sources=rag_sources,
        )
        run = await run_project_analysis(
            input_payload,
            tool_context=tool_context,
            rag_sources=rag_sources,
        )
    except Exception as exc:
        error = _error_payload("analysis_error", exc)
        run = ProjectAnalysisRun(
            report=build_failed_report(
                str(exc),
                mcp_evidence=tool_context.mcp_evidence,
                rag_sources=rag_sources,
            ),
            model=settings.agent_model,
            reasoning_effort=settings.reasoning_effort,
            response_id=None,
            trace_id=None,
            usage=None,
            error=error,
        )

    return await _persist_analysis(db, post, run, tool_context.mcp_evidence)


async def get_latest_analysis_for_post(db: AsyncSession, post_id: int) -> PersistedAnalysis:
    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    stmt = (
        select(AiReport)
        .where(AiReport.post_id == post_id)
        .order_by(AiReport.created_at.desc(), AiReport.id.desc())
        .limit(1)
    )
    ai_report = (await db.execute(stmt)).scalar_one_or_none()
    if ai_report is None:
        raise AnalysisReportNotFoundError(post_id)

    report = _report_from_db(ai_report)
    return PersistedAnalysis(
        status=ai_report.status,  # type: ignore[arg-type]
        report_id=ai_report.id,
        report=report,
        model=ai_report.model,
        reasoning_effort=ai_report.reasoning_effort,
        response_id=ai_report.response_id,
        trace_id=ai_report.trace_id,
        usage=ai_report.usage,
        error=ai_report.error,
        created_at=ai_report.created_at,
    )


async def _load_post(db: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.author), selectinload(Post.tags))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _missing_required_fields(post: Post) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    questions: list[str] = []

    if not (post.title or "").strip():
        missing.append("title")
        questions.append("프로젝트 이름이나 제목을 적어주세요.")
    has_external_source = bool((post.service_url or "").strip() or (post.github_url or "").strip())
    description_text = f"{post.one_liner or ''}\n{post.body or ''}".strip()
    if not has_external_source and len(description_text) < 200:
        missing.append("body")
        questions.append("배포 URL, GitHub URL, 또는 200자 이상의 프로젝트 설명을 추가해주세요.")

    return missing, questions


async def _persist_analysis(
    db: AsyncSession,
    post: Post,
    run: ProjectAnalysisRun,
    mcp_evidence: list[CollectedMcpEvidence],
) -> PersistedAnalysis:
    status = run.report.status.status
    ai_report = AiReport(
        post_id=post.id,
        status=status,
        report_type="full_analysis",
        model=run.model,
        reasoning_effort=run.reasoning_effort,
        response_id=run.response_id,
        trace_id=run.trace_id,
        usage=run.usage,
        input_snapshot=build_runner_input(
            post=_post_snapshot(post),
            mcp_evidence=mcp_evidence,
            rag_sources=run.report.evidence.rag_sources,
        ),
        report=run.report.model_dump(mode="json"),
        error=run.error,
    )
    db.add(ai_report)
    await db.flush()

    for item in mcp_evidence:
        await record_mcp_evidence(
            db,
            tool_name=item.tool_name,
            arguments=item.arguments,
            result=item.result,
            success=item.success,
            error_message=item.error_message,
            post_id=post.id,
            report_id=ai_report.id,
        )

    await index_ai_report_embedding(db, ai_report, run.report)

    post.analysis_status = _post_status_for_report(status)
    post.ai_summary = _summary_for_post(run.report)
    await db.commit()
    await db.refresh(ai_report)

    return PersistedAnalysis(
        status=status,
        report_id=ai_report.id,
        report=run.report,
        model=run.model,
        reasoning_effort=run.reasoning_effort,
        response_id=run.response_id,
        trace_id=run.trace_id,
        usage=run.usage,
        error=run.error,
        created_at=ai_report.created_at,
    )


def _post_status_for_report(status: ReportStatus) -> str:
    if status == "refused":
        return "failed"
    return status


def _summary_for_post(report: ProjectAnalysisReport) -> str:
    if report.status.status == "failed":
        return "AI 분석 실패"
    if report.status.status == "refused":
        return "AI 분석 거절"
    return report.service_understanding.one_line_summary


def _post_snapshot(post: Post) -> dict[str, Any]:
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "post_type": post.post_type,
        "service_url": post.service_url,
        "github_url": post.github_url,
        "one_liner": post.one_liner,
        "target_user": post.target_user,
        "tech_stack": post.tech_stack or [],
        "tags": [tag.slug for tag in post.tags],
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


def _report_from_db(ai_report: AiReport) -> ProjectAnalysisReport:
    if ai_report.report:
        return ProjectAnalysisReport.model_validate(ai_report.report)
    return build_failed_report("stored report payload is empty")


def _error_payload(error_type: str, exc: Exception) -> dict[str, Any]:
    return {
        "type": error_type,
        "message": str(exc),
        "exception": exc.__class__.__name__,
    }
