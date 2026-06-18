from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
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
    merge_report_evidence,
    run_project_analysis,
)
from app.ai.tools import call_projectlens_mcp_tool
from app.ai.schemas import ProjectAnalysisReport, ReportStatus
from app.config import settings
from app.mcp_client.client import record_mcp_evidence
from app.mcp_client.tools import (
    CHECK_DEPLOY_STATUS,
    FETCH_GITHUB_README,
    FETCH_RENDERED_SITE_OVERVIEW,
    FETCH_SITE_CONTEXT,
    FETCH_SITE_OVERVIEW,
)
from app.models import AiReport, Post
from app.rag.indexer import index_ai_report_embedding, index_post_embedding
from app.rag.retriever import retrieve_similar_projects

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class AnalysisJobState:
    post_id: int
    status: str
    latest_report_id: int | None
    latest_report_status: str | None


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
        post, rag_sources = await _prepare_rag_context(db, post)
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
        rendered_fallback_collected = await _collect_rendered_site_fallback_if_needed(
            post,
            run,
            tool_context,
        )
        if rendered_fallback_collected:
            run = ProjectAnalysisRun(
                report=merge_report_evidence(
                    run.report,
                    mcp_evidence=tool_context.mcp_evidence,
                    rag_sources=rag_sources,
                ),
                model=run.model,
                reasoning_effort=run.reasoning_effort,
                response_id=run.response_id,
                trace_id=run.trace_id,
                usage=run.usage,
                error=run.error,
            )
        run = _force_failed_if_external_evidence_unusable(post, run, tool_context.mcp_evidence)
    except Exception as exc:
        await _collect_failure_evidence_if_empty(post, tool_context)
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

    ai_report = await _load_latest_ai_report(db, post_id)
    if ai_report is None:
        raise AnalysisReportNotFoundError(post_id)
    if _is_transient_connection_failure(ai_report):
        completed_report = await _load_latest_completed_ai_report(db, post_id)
        if completed_report is not None:
            ai_report = completed_report

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


async def _prepare_rag_context(
    db: AsyncSession,
    post: Post,
) -> tuple[Post, list]:
    try:
        await index_post_embedding(db, post)
        return post, await retrieve_similar_projects(db, post)
    except Exception:
        logger.exception(
            "failed to prepare RAG context; continuing analysis without similar projects: post_id=%s",
            post.id,
        )
        await db.rollback()
        reloaded_post = await _load_post(db, post.id)
        return reloaded_post or post, []


async def _collect_failure_evidence_if_empty(
    post: Post,
    tool_context: AnalysisToolContext,
) -> None:
    if tool_context.mcp_evidence:
        return

    service_url = (post.service_url or "").strip()
    if service_url:
        for tool_name in (CHECK_DEPLOY_STATUS, FETCH_SITE_OVERVIEW, FETCH_SITE_CONTEXT):
            await call_projectlens_mcp_tool(
                tool_context,
                tool_name,
                {"url": post.service_url},
                expected_url=tool_context.service_url,
            )

    github_url = (post.github_url or "").strip()
    if github_url:
        await call_projectlens_mcp_tool(
            tool_context,
            FETCH_GITHUB_README,
            {"github_url": post.github_url},
            expected_url=tool_context.github_url,
        )


async def start_analysis_job_for_post(db: AsyncSession, post_id: int) -> AnalysisJobState:
    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    post.analysis_status = "running"
    await db.commit()
    return await get_analysis_job_status_for_post(db, post_id)


async def get_analysis_job_status_for_post(db: AsyncSession, post_id: int) -> AnalysisJobState:
    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    ai_report = await _load_latest_ai_report(db, post_id)
    return AnalysisJobState(
        post_id=post.id,
        status=post.analysis_status,
        latest_report_id=ai_report.id if ai_report else None,
        latest_report_status=ai_report.status if ai_report else None,
    )


async def mark_analysis_job_failed(
    db: AsyncSession,
    post_id: int,
    message: str,
    *,
    exc: Exception | None = None,
) -> None:
    post = await _load_post(db, post_id)
    if post is None:
        raise AnalysisPostNotFoundError(post_id)

    report = build_failed_report(message)
    error = _error_payload("analysis_job_error", exc) if exc else {
        "type": "analysis_job_error",
        "message": message,
    }
    ai_report = AiReport(
        post_id=post.id,
        status="failed",
        report_type="full_analysis",
        model=settings.agent_model,
        reasoning_effort=settings.reasoning_effort,
        response_id=None,
        trace_id=None,
        usage=None,
        input_snapshot=build_runner_input(
            post=_post_snapshot(post),
            mcp_evidence=[],
            rag_sources=[],
        ),
        report=report.model_dump(mode="json"),
        error=error,
    )
    db.add(ai_report)
    post.analysis_status = "failed"
    post.ai_summary = message
    await db.commit()


async def _load_post(db: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.author), selectinload(Post.tags))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _load_latest_ai_report(db: AsyncSession, post_id: int) -> AiReport | None:
    stmt = (
        select(AiReport)
        .where(AiReport.post_id == post_id)
        .order_by(AiReport.created_at.desc(), AiReport.id.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _load_latest_completed_ai_report(db: AsyncSession, post_id: int) -> AiReport | None:
    stmt = (
        select(AiReport)
        .where(AiReport.post_id == post_id, AiReport.status == "completed")
        .order_by(AiReport.created_at.desc(), AiReport.id.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _is_transient_connection_failure(ai_report: AiReport) -> bool:
    if ai_report.status != "failed" or not isinstance(ai_report.error, dict):
        return False
    error_type = str(ai_report.error.get("type") or "")
    exception = str(ai_report.error.get("exception") or "")
    message = str(ai_report.error.get("message") or "")
    return (
        error_type == "analysis_error"
        and (
            exception == "APIConnectionError"
            or "Connection error" in message
            or "connection error" in message.lower()
        )
    )


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

    post.analysis_status = _post_status_for_report(status)
    post.ai_summary = _summary_for_post(run.report)
    await db.commit()
    await db.refresh(ai_report)

    try:
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
        await db.commit()
    except Exception:
        logger.exception(
            "failed to persist MCP evidence after report save: post_id=%s report_id=%s",
            post.id,
            ai_report.id,
        )
        await db.rollback()

    try:
        await index_ai_report_embedding(db, ai_report, run.report)
        await db.commit()
    except Exception:
        logger.exception(
            "failed to index analysis report embedding after report save: post_id=%s report_id=%s",
            post.id,
            ai_report.id,
        )
        await db.rollback()

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
        return "분석 범위 한계"
    if report.status.status == "refused":
        return "분석 제공 불가"
    return report.summary.one_line_review or report.service_understanding.one_line_summary


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


async def _collect_rendered_site_fallback_if_needed(
    post: Post,
    run: ProjectAnalysisRun,
    tool_context: AnalysisToolContext,
) -> bool:
    if run.report.status.status != "completed":
        return False
    if not (post.service_url or "").strip():
        return False
    if any(item.tool_name == FETCH_RENDERED_SITE_OVERVIEW for item in tool_context.mcp_evidence):
        return False
    if not _service_url_reachable(post, tool_context.mcp_evidence):
        return False

    site_text_tools = {FETCH_SITE_OVERVIEW, FETCH_SITE_CONTEXT}
    site_text_items = [
        item for item in tool_context.mcp_evidence
        if item.tool_name in site_text_tools
    ]
    if any(_mcp_item_has_usable_text_result(item) for item in site_text_items):
        return False

    await call_projectlens_mcp_tool(
        tool_context,
        FETCH_RENDERED_SITE_OVERVIEW,
        {"url": post.service_url},
        expected_url=tool_context.service_url,
    )
    return True


def _force_failed_if_external_evidence_unusable(
    post: Post,
    run: ProjectAnalysisRun,
    mcp_evidence: list[CollectedMcpEvidence],
) -> ProjectAnalysisRun:
    if run.report.status.status != "completed":
        return run
    if _service_url_failed(post, mcp_evidence):
        message = (
            "배포 URL에 접근하지 못해 화면 분석을 수행하지 못했습니다. "
            "프로젝트 설명을 조금 더 자세히 입력하거나 접속 가능한 배포 URL을 다시 제출해주세요."
        )
        report = build_failed_report(
            message,
            mcp_evidence=mcp_evidence,
            rag_sources=run.report.evidence.rag_sources,
        )
        return ProjectAnalysisRun(
            report=report,
            model=run.model,
            reasoning_effort=run.reasoning_effort,
            response_id=run.response_id,
            trace_id=run.trace_id,
            usage=run.usage,
            error=run.error
            or {
                "type": "service_url_unreachable",
                "message": message,
            },
        )
    if _has_sufficient_written_context(post):
        return run
    expected_tools = _expected_external_tools(post)
    if not expected_tools:
        return run

    relevant_evidence = [item for item in mcp_evidence if item.tool_name in expected_tools]
    has_textual_evidence = any(_mcp_item_has_usable_text_result(item) for item in relevant_evidence)
    if has_textual_evidence:
        return run

    if _external_site_blocked(post, mcp_evidence):
        missing_fields = ["github_url", "detailed_description"]
        questions = [
            "사이트가 자동 수집을 차단했습니다. 공개 GitHub 저장소나 README URL을 추가해 주세요.",
            "또는 서비스 화면/기능/사용자 흐름을 200자 이상으로 자세히 적어 주세요.",
            "공식 API나 허가된 데이터 경로가 있다면 그 링크도 함께 제출해 주세요.",
        ]
        report = build_need_more_info_report(
            missing_fields,
            questions,
            mcp_evidence=mcp_evidence,
            rag_sources=run.report.evidence.rag_sources,
        )
        return ProjectAnalysisRun(
            report=report,
            model=run.model,
            reasoning_effort=run.reasoning_effort,
            response_id=run.response_id,
            trace_id=run.trace_id,
            usage=run.usage,
            error=run.error
            or {
                "type": "blocked_by_site",
                "message": "Submitted site blocks automated evidence collection.",
            },
        )

    message = (
        "제출된 URL/GitHub에서 분석 가능한 외부 근거를 가져오지 못했습니다. "
        "접속 가능한 배포 URL, 공개 GitHub 저장소, 또는 더 긴 프로젝트 설명이 필요합니다."
    )
    report = build_failed_report(
        message,
        mcp_evidence=mcp_evidence,
        rag_sources=run.report.evidence.rag_sources,
    )
    return ProjectAnalysisRun(
        report=report,
        model=run.model,
        reasoning_effort=run.reasoning_effort,
        response_id=run.response_id,
        trace_id=run.trace_id,
        usage=run.usage,
        error=run.error
        or {
            "type": "external_evidence_unavailable",
            "message": message,
        },
    )


def _has_sufficient_written_context(post: Post) -> bool:
    description_text = f"{post.one_liner or ''}\n{post.body or ''}".strip()
    return len(description_text) >= 200


def _expected_external_tools(post: Post) -> set[str]:
    tools: set[str] = set()
    if (post.service_url or "").strip():
        tools.update({
            CHECK_DEPLOY_STATUS,
            FETCH_SITE_OVERVIEW,
            FETCH_SITE_CONTEXT,
            FETCH_RENDERED_SITE_OVERVIEW,
        })
    if (post.github_url or "").strip():
        tools.add(FETCH_GITHUB_README)
    return tools


def _service_url_failed(post: Post, mcp_evidence: list[CollectedMcpEvidence]) -> bool:
    if not (post.service_url or "").strip():
        return False
    deploy_checks = [item for item in mcp_evidence if item.tool_name == CHECK_DEPLOY_STATUS]
    if not deploy_checks:
        return False
    return all(not _mcp_deploy_check_reachable(item) for item in deploy_checks)


def _service_url_reachable(post: Post, mcp_evidence: list[CollectedMcpEvidence]) -> bool:
    if not (post.service_url or "").strip():
        return False
    deploy_checks = [item for item in mcp_evidence if item.tool_name == CHECK_DEPLOY_STATUS]
    return any(_mcp_deploy_check_reachable(item) for item in deploy_checks)


def _mcp_deploy_check_reachable(item: CollectedMcpEvidence) -> bool:
    if not item.success:
        return False
    if item.tool_name == CHECK_DEPLOY_STATUS and isinstance(item.result, dict):
        return bool(item.result.get("is_reachable"))
    return False


def _mcp_item_has_usable_text_result(item: CollectedMcpEvidence) -> bool:
    if not item.success or not isinstance(item.result, dict):
        return False
    if item.tool_name == FETCH_SITE_OVERVIEW:
        return _combined_text_length(
            item.result,
            ("title", "description", "h1", "main_text"),
        ) >= 80
    if item.tool_name == FETCH_GITHUB_README:
        return _combined_text_length(
            item.result,
            ("description", "readme", "language", "topics"),
        ) >= 80
    if item.tool_name == FETCH_SITE_CONTEXT:
        pages = item.result.get("pages")
        if not isinstance(pages, list):
            return False
        total = 0
        for page in pages:
            if not isinstance(page, dict):
                continue
            total += _combined_text_length(
                page,
                ("title", "description", "h1", "main_text"),
            )
        return total >= 80
    if item.tool_name == FETCH_RENDERED_SITE_OVERVIEW:
        if bool(item.result.get("blocked_by_site")):
            return False
        return _combined_text_length(
            item.result,
            ("title", "description", "h1", "visible_text"),
        ) >= 80
    return False


def _external_site_blocked(post: Post, mcp_evidence: list[CollectedMcpEvidence]) -> bool:
    if not (post.service_url or "").strip():
        return False
    for item in mcp_evidence:
        if item.tool_name != FETCH_RENDERED_SITE_OVERVIEW:
            continue
        if item.success and isinstance(item.result, dict) and item.result.get("blocked_by_site"):
            return True
    return False


def _combined_text_length(payload: dict[str, Any], keys: tuple[str, ...]) -> int:
    parts: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return len(" ".join(part.strip() for part in parts if part.strip()))


def _report_from_db(ai_report: AiReport) -> ProjectAnalysisReport:
    if ai_report.report:
        report = ProjectAnalysisReport.model_validate(ai_report.report)
        normalized_report = merge_report_evidence(
            report,
            mcp_evidence=[],
            rag_sources=report.evidence.rag_sources,
        )
        if normalized_report.report_version != "2.0":
            return normalized_report.model_copy(update={"report_version": "2.0"})
        return normalized_report
    return build_failed_report("stored report payload is empty")


def _error_payload(error_type: str, exc: Exception) -> dict[str, Any]:
    return {
        "type": error_type,
        "message": str(exc),
        "exception": exc.__class__.__name__,
    }
