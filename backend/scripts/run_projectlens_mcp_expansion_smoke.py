from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
MCP_ROOT = PROJECT_ROOT / "mcp-server"
os.chdir(BACKEND_ROOT)
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(MCP_ROOT))

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import runner as runner_module
from app.ai.context import AnalysisToolContext, CollectedMcpEvidence
from app.auth.security import hash_password
from app.config import settings
from app.db import SessionLocal
from app.mcp_client.tools import (
    CAPTURE_SCREENSHOT,
    FETCH_SITE_CONTEXT,
    RUN_LIGHTHOUSE_SUMMARY,
)
from app.models import AiReport, Embedding, McpEvidence, Post, User
from app.repositories import users as users_repo
from app.schemas import PostCreate
from app.services import analysis_service
from app.services import posts as posts_service
from tools.lighthouse import run_lighthouse_summary
from tools.screenshot import capture_screenshot
from tools.site_context import fetch_site_context


Q10_MARKER = "[Q6_Q11_MCP_SMOKE:"

AUTHOR = {
    "username": "projectlens_mcp_expansion_smoke",
    "email": "projectlens.mcp.expansion.smoke@example.invalid",
    "password": "ProjectLensMcpExpansionLocalOnly!456",
}


@dataclass(frozen=True)
class SmokePost:
    slug: str
    title: str
    body: str
    one_liner: str
    service_url: str | None = None
    github_url: str | None = None
    target_user: str = "ProjectLens 운영자"
    tech_stack: list[str] | None = None


SMOKE_POSTS = {
    "completed": SmokePost(
        slug="completed",
        title="[Q10 Smoke] MCP expansion completed path",
        service_url="https://example.com/",
        one_liner="새 MCP evidence가 저장되고 최신 리포트에 병합되는지 확인.",
        body=(
            "Q6부터 Q10까지 추가된 site_context, screenshot, Lighthouse evidence가 전체 분석을 깨뜨리지 "
            "않고 mcp_evidences와 latest report에 남는지 확인하는 입력입니다. example.com은 얇은 공개 "
            "페이지라 site_context가 최소 1페이지 evidence를 제공하고, screenshot/Lighthouse는 환경에 "
            "따라 성공 또는 graceful 실패로 저장될 수 있어야 합니다. "
            f"{Q10_MARKER}completed]"
        ),
        tech_stack=["MCP", "Smoke Test"],
    ),
    "failed": SmokePost(
        slug="failed",
        title="[Q10 Smoke] MCP expansion SSRF failed path",
        service_url="http://127.0.0.1:8000",
        one_liner="SSRF 차단 URL이 failed 리포트와 실패 evidence로 저장되는지 확인.",
        body=(
            "localhost URL은 SSRF 정책상 차단되어야 하며, 새 MCP 도구가 추가되어도 전체 분석은 깨지지 "
            "않고 failed 리포트로 저장되어야 합니다. "
            f"{Q10_MARKER}failed]"
        ),
        tech_stack=["MCP", "SSRF", "Smoke Test"],
    ),
    "need_more_info": SmokePost(
        slug="need-more-info",
        title="[Q10 Smoke] Need more info",
        one_liner="정보 부족 상태 확인.",
        body=f"짧음. {Q10_MARKER}need-more-info]",
        tech_stack=["MCP", "Smoke Test"],
    ),
    "optional_failure": SmokePost(
        slug="optional-failure",
        title="[Q10 Smoke] Optional MCP failure does not crash",
        service_url="https://example.com/",
        one_liner="선택 MCP 도구 실패가 completed 분석을 막지 않는지 확인.",
        body=(
            "Lighthouse 같은 선택 MCP 도구가 실패해도 배포 상태와 사이트 텍스트 evidence가 충분하면 "
            "분석은 completed로 끝나야 합니다. 실패는 success=false evidence로만 남깁니다. "
            f"{Q10_MARKER}optional-failure]"
        ),
        tech_stack=["MCP", "Optional Failure", "Smoke Test"],
    ),
}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run ProjectLens Q6-Q11 MCP expansion smoke checks.")
    parser.add_argument("--keep-existing", action="store_true")
    parser.add_argument(
        "--fail-under-threshold",
        action="store_true",
        help="Exit with status 1 if any MCP expansion smoke check fails.",
    )
    args = parser.parse_args()

    settings.openai_api_key = None
    os.environ.pop("OPENAI_API_KEY", None)

    direct_tools = await run_direct_tool_checks()
    async with SessionLocal() as session:
        if not args.keep_existing:
            await cleanup_previous_rows(session)

        user = await ensure_user(session, **AUTHOR)
        await session.commit()

        completed = await run_analysis_case(session, user.id, SMOKE_POSTS["completed"])
        failed = await run_analysis_case(session, user.id, SMOKE_POSTS["failed"])
        need_more = await run_analysis_case(session, user.id, SMOKE_POSTS["need_more_info"])
        optional_failure = await run_optional_failure_case(session, user.id)
        async_job = await run_async_job_case(session, user.id)

    checks = {
        "direct_tools": direct_tools,
        "evidence_persistence_and_latest_report": {
            "results": completed,
            "passed": (
                completed["status"] == "completed"
                and completed["latest_report_id"] == completed["report_id"]
                and completed["new_tool_rows_present"]
                and completed["new_tool_sources_present"]
                and completed["successful_lighthouse_summary_persisted"]
            ),
        },
        "ssrf_failed_analysis_path": {
            "results": failed,
            "passed": (
                failed["status"] == "failed"
                and failed["mcp_failure_by_tool"].get(FETCH_SITE_CONTEXT, 0) >= 1
            ),
        },
        "need_more_info_path": {
            "results": need_more,
            "passed": need_more["status"] == "need_more_info" and need_more["mcp_evidence_count"] == 0,
        },
        "optional_tool_failure_no_crash": {
            "results": optional_failure,
            "passed": (
                optional_failure["status"] == "completed"
                and optional_failure["mcp_failure_by_tool"].get(RUN_LIGHTHOUSE_SUMMARY, 0) >= 1
            ),
        },
        "async_job_status_polling": {
            "results": async_job,
            "passed": (
                async_job["start_status"] == "running"
                and async_job["observed_running_before_completion"]
                and async_job["final_status"] == "completed"
                and async_job["latest_report_id"] == async_job["report_id"]
            ),
        },
    }
    passed = all(item["passed"] for item in checks.values())
    summary = {
        "mode": "mock_model_with_real_mcp_tools",
        "passed": passed,
        "checks": checks,
        "q11_latency": {
            "analysis_elapsed_ms": [
                completed["elapsed_ms"],
                failed["elapsed_ms"],
                need_more["elapsed_ms"],
                optional_failure["elapsed_ms"],
            ],
            "over_15s_count": sum(
                1
                for value in (
                    completed["elapsed_ms"],
                    failed["elapsed_ms"],
                    need_more["elapsed_ms"],
                    optional_failure["elapsed_ms"],
                )
                if value > 15_000
            ),
        },
    }
    summary["q11_latency"]["async_jobs_implemented"] = checks["async_job_status_polling"]["passed"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    if args.fail_under_threshold and not passed:
        raise SystemExit(1)


async def run_direct_tool_checks() -> dict[str, Any]:
    context = await fetch_site_context("https://example.com/")
    context_ssrf = await fetch_site_context("http://127.0.0.1:8000")
    screenshot = await capture_screenshot("https://example.com/")
    screenshot_ssrf = await capture_screenshot("http://127.0.0.1:8000")
    lighthouse = await run_lighthouse_summary("https://example.com/")
    lighthouse_ssrf = await run_lighthouse_summary("http://127.0.0.1:8000")

    screenshot_has_no_bytes = not any(
        key in screenshot for key in ("image_bytes", "image_base64", "base64", "raw_image")
    )
    lighthouse_has_no_raw_report = not any(
        key in lighthouse for key in ("raw_report", "report", "lhr", "html")
    )
    return {
        "results": {
            "fetch_site_context": context,
            "fetch_site_context_ssrf": context_ssrf,
            "capture_screenshot": _compact_direct_tool_result(screenshot),
            "capture_screenshot_ssrf": screenshot_ssrf,
            "run_lighthouse_summary": _compact_direct_tool_result(lighthouse),
            "run_lighthouse_summary_ssrf": lighthouse_ssrf,
        },
        "passed": (
            context.get("success") is True
            and 1 <= int(context.get("page_count") or 0) <= 5
            and context_ssrf.get("success") is False
            and screenshot_has_no_bytes
            and screenshot_ssrf.get("success") is False
            and lighthouse_has_no_raw_report
            and lighthouse_ssrf.get("success") is False
            and (
                lighthouse.get("success") is False
                or isinstance(lighthouse.get("scores"), dict)
            )
        ),
    }


def _compact_direct_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = dict(result)
    if "visible_text_sample" in compact:
        compact["visible_text_sample"] = str(compact["visible_text_sample"])[:120]
    return compact


async def cleanup_previous_rows(session: AsyncSession) -> None:
    smoke_post_ids = select(Post.id).where(Post.body.contains(Q10_MARKER)).subquery()
    smoke_report_ids = select(AiReport.id).where(
        AiReport.post_id.in_(select(smoke_post_ids.c.id))
    ).subquery()
    await session.execute(
        delete(McpEvidence).where(
            or_(
                McpEvidence.post_id.in_(select(smoke_post_ids.c.id)),
                McpEvidence.report_id.in_(select(smoke_report_ids.c.id)),
            )
        )
    )
    await session.execute(
        delete(Embedding).where(
            or_(
                (Embedding.source_type == "post")
                & (Embedding.source_id.in_(select(smoke_post_ids.c.id))),
                (Embedding.source_type == "ai_report")
                & (Embedding.source_id.in_(select(smoke_report_ids.c.id))),
            )
        )
    )
    await session.execute(delete(Post).where(Post.id.in_(select(smoke_post_ids.c.id))))
    await session.commit()


async def ensure_user(session: AsyncSession, *, username: str, email: str, password: str) -> User:
    user = await users_repo.get_by_username(session, username)
    if user is not None:
        return user
    return await users_repo.create_user(
        session,
        username=username,
        email=email,
        password_hash=hash_password(password),
    )


async def insert_smoke_post(session: AsyncSession, author_id: int, smoke: SmokePost) -> Post:
    body = PostCreate(
        title=smoke.title,
        body=smoke.body,
        postType="project",
        serviceUrl=smoke.service_url,
        githubUrl=smoke.github_url,
        oneLiner=smoke.one_liner,
        targetUser=smoke.target_user,
        techStack=smoke.tech_stack or ["MCP Smoke Test"],
        tagIds=[],
    )
    post = await posts_service.create(session, body, author_id=author_id)
    await session.commit()
    return post


async def run_analysis_case(session: AsyncSession, author_id: int, smoke: SmokePost) -> dict[str, Any]:
    post = await insert_smoke_post(session, author_id, smoke)
    started = time.perf_counter()
    result = await analysis_service.run_analysis_for_post(session, post.id)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    latest = await analysis_service.get_latest_analysis_for_post(session, post.id)
    db_post = await session.get(Post, post.id)
    evidence_rows = (
        await session.execute(
            select(McpEvidence)
            .where(McpEvidence.post_id == post.id)
            .order_by(McpEvidence.id)
        )
    ).scalars().all()
    success_by_tool: dict[str, int] = {}
    failure_by_tool: dict[str, int] = {}
    for row in evidence_rows:
        bucket = success_by_tool if row.success else failure_by_tool
        bucket[row.tool_name] = bucket.get(row.tool_name, 0) + 1
    mcp_source_kinds = {
        source.evidence_kind
        for source in result.report.evidence.mcp_sources
    }
    new_tool_rows_present = all(
        (success_by_tool.get(tool, 0) + failure_by_tool.get(tool, 0)) >= 1
        for tool in (FETCH_SITE_CONTEXT, CAPTURE_SCREENSHOT, RUN_LIGHTHOUSE_SUMMARY)
    )
    new_tool_sources_present = {"site_context", "screenshot", "lighthouse"}.issubset(mcp_source_kinds)
    successful_lighthouse_summary_persisted = _successful_lighthouse_summary_persisted(evidence_rows)
    return {
        "post_id": post.id,
        "report_id": result.report_id,
        "latest_report_id": latest.report_id,
        "status": result.status,
        "latest_status": latest.status,
        "post_analysis_status": db_post.analysis_status if db_post else None,
        "mcp_evidence_count": len(evidence_rows),
        "mcp_success_by_tool": success_by_tool,
        "mcp_failure_by_tool": failure_by_tool,
        "mcp_source_kinds": sorted(mcp_source_kinds),
        "new_tool_rows_present": new_tool_rows_present,
        "new_tool_sources_present": new_tool_sources_present,
        "successful_lighthouse_summary_persisted": successful_lighthouse_summary_persisted,
        "elapsed_ms": elapsed_ms,
    }


def _successful_lighthouse_summary_persisted(evidence_rows: list[McpEvidence]) -> bool:
    lighthouse_rows = [
        row for row in evidence_rows
        if row.tool_name == RUN_LIGHTHOUSE_SUMMARY and row.success
    ]
    if not lighthouse_rows:
        return True
    for row in lighthouse_rows:
        result = row.result if isinstance(row.result, dict) else {}
        scores = result.get("scores")
        key_audits = result.get("key_audits")
        if not isinstance(scores, dict) or not any(
            isinstance(value, (int, float)) for value in scores.values()
        ):
            return False
        if not isinstance(key_audits, list) or not key_audits:
            return False
    return True


async def run_optional_failure_case(session: AsyncSession, author_id: int) -> dict[str, Any]:
    original_call = runner_module.call_projectlens_mcp_tool

    async def fail_lighthouse(
        context: AnalysisToolContext,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        expected_url: str | None,
    ) -> dict[str, Any]:
        if tool_name == RUN_LIGHTHOUSE_SUMMARY:
            result = {
                "success": False,
                "url": arguments.get("url"),
                "error_message": "Injected optional Lighthouse failure for Q10 smoke.",
            }
            context.mcp_evidence.append(
                CollectedMcpEvidence(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    success=False,
                    error_message=str(result["error_message"]),
                )
            )
            return result
        return await original_call(
            context,
            tool_name,
            arguments,
            expected_url=expected_url,
        )

    runner_module.call_projectlens_mcp_tool = fail_lighthouse
    try:
        return await run_analysis_case(session, author_id, SMOKE_POSTS["optional_failure"])
    finally:
        runner_module.call_projectlens_mcp_tool = original_call


async def run_async_job_case(session: AsyncSession, author_id: int) -> dict[str, Any]:
    post = await insert_smoke_post(session, author_id, SMOKE_POSTS["completed"])
    start_started = time.perf_counter()
    start_state = await analysis_service.start_analysis_job_for_post(session, post.id)
    start_elapsed_ms = int((time.perf_counter() - start_started) * 1000)

    async def run_in_job_session():
        async with SessionLocal() as task_session:
            return await analysis_service.run_analysis_for_post(task_session, post.id)

    task = asyncio.create_task(run_in_job_session())
    await asyncio.sleep(0.05)
    async with SessionLocal() as observed_session:
        observed_state = await analysis_service.get_analysis_job_status_for_post(observed_session, post.id)
    result = await task
    async with SessionLocal() as final_session:
        final_state = await analysis_service.get_analysis_job_status_for_post(final_session, post.id)
        latest = await analysis_service.get_latest_analysis_for_post(final_session, post.id)
    return {
        "post_id": post.id,
        "start_status": start_state.status,
        "start_elapsed_ms": start_elapsed_ms,
        "observed_status_before_completion": observed_state.status,
        "observed_running_before_completion": observed_state.status == "running",
        "final_status": final_state.status,
        "report_id": result.report_id,
        "latest_report_id": latest.report_id,
    }


if __name__ == "__main__":
    asyncio.run(main())
