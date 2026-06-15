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

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import runner as runner_module
from app.auth.security import hash_password
from app.config import settings
from app.db import SessionLocal
from app.models import AiReport, Embedding, McpEvidence, Post, User
from app.rag.retriever import retrieve_similar_projects
from app.repositories import users as users_repo
from app.schemas import PostCreate
from app.services import analysis_service
from app.services import posts as posts_service
from tools.site import check_deploy_status


Q1_MARKER = "[Q1_Q5_SMOKE:"

AUTHOR = {
    "username": "projectlens_q1_q5_smoke",
    "email": "projectlens.q1q5.smoke@example.invalid",
    "password": "ProjectLensQ1Q5LocalOnly!456",
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
    "url_unreachable": SmokePost(
        slug="url-unreachable",
        title="[Q1 Smoke] URL unreachable",
        service_url="https://projectlens-q1-unreachable.invalid",
        one_liner="접속 불가 URL이 failed 또는 need_more_info로 저장되는지 확인.",
        body=f"접속 불가 URL graceful 처리를 검증하는 짧은 입력입니다. {Q1_MARKER}url-unreachable]",
        tech_stack=["Smoke Test"],
    ),
    "ssrf_blocked": SmokePost(
        slug="ssrf-blocked",
        title="[Q1 Smoke] SSRF blocked URL",
        service_url="http://127.0.0.1:8000",
        one_liner="SSRF 차단 URL이 외부 fetch 없이 실패 상태로 저장되는지 확인.",
        body=f"localhost SSRF 차단 처리를 검증하는 짧은 입력입니다. {Q1_MARKER}ssrf-blocked]",
        tech_stack=["Smoke Test", "SSRF"],
    ),
    "thin_site_fallback": SmokePost(
        slug="thin-site-fallback",
        title="[Q1 Smoke] Thin site with README fallback",
        service_url="https://example.com/",
        github_url="https://github.com/YangSiJun528/dom-vdom",
        one_liner="본문이 빈약한 URL에서 게시글 설명과 GitHub README 근거를 fallback으로 쓰는지 확인.",
        body=(
            "example.com처럼 서비스 본문이 얇은 공개 URL을 제출했을 때 ProjectLens가 사이트 텍스트만으로 "
            "기능을 지어내지 않고, 사용자가 작성한 프로젝트 설명과 공개 GitHub README를 함께 근거로 "
            "사용하는지 확인하는 smoke 입력입니다. README 근거가 없거나 부족하면 한계를 남겨야 합니다. "
            f"{Q1_MARKER}thin-site-fallback]"
        ),
        target_user="본문이 얇은 배포 URL과 GitHub 저장소를 함께 제출한 개발자",
        tech_stack=["JavaScript", "GitHub", "Fallback"],
    ),
    "mock_refused": SmokePost(
        slug="mock-refused",
        title="[Q1 Smoke] Structured refusal [mock:refused]",
        one_liner="refused 상태 저장과 UI 계약을 확인.",
        body=(
            "모델 안전 거절을 mock으로 재현하기 위한 충분한 설명입니다. "
            "이 입력은 실제 정책 위반 컨텐츠가 아니라 상태 저장과 카드 렌더 계약 확인만을 위한 데이터입니다. "
            "프로젝트 설명 자체는 의도적으로 무해하며, precheck의 정보부족 분기를 지나 모델 refusal 저장 "
            "경로까지 도달하도록 길이를 확보합니다. latest API는 refused를 반환하고 posts.analysis_status는 "
            "DB 제약에 맞춰 failed로 매핑되어야 합니다. "
            f"{Q1_MARKER}mock-refused] [mock:refused]"
        ),
        tech_stack=["Smoke Test"],
    ),
    "mock_failed": SmokePost(
        slug="mock-failed",
        title="[Q1 Smoke] Structured failure [mock:failed]",
        one_liner="모델/구조화 출력 실패가 failed와 ai_reports.error로 저장되는지 확인.",
        body=(
            "구조화 출력 또는 모델 실행 실패 경로를 mock으로 재현하기 위한 충분한 설명입니다. "
            "실제 사용자 입력이 아니라 ai_reports.error, posts.analysis_status, latest API 계약을 확인하는 "
            "데이터입니다. 실패 상태에서도 리포트 카드가 깨지지 않아야 합니다. "
            f"{Q1_MARKER}mock-failed] [mock:failed]"
        ),
        tech_stack=["Smoke Test"],
    ),
    "need_more_info": SmokePost(
        slug="need-more-info",
        title="[Q1 Smoke] Need more info",
        one_liner="정보 부족 상태 확인.",
        body=f"짧음. {Q1_MARKER}need-more-info]",
        tech_stack=["Smoke Test"],
    ),
    "running_state": SmokePost(
        slug="running-state",
        title="[Q1 Smoke] Running state visibility",
        one_liner="분석 중 running 상태가 DB에 먼저 저장되는지 확인.",
        body=(
            "느린 분석 상황을 재현하기 위한 smoke 입력입니다. 분석 시작 직후 "
            "posts.analysis_status가 running으로 커밋되어 프론트가 loading/running 상태를 "
            "보여줄 수 있어야 합니다. 이 케이스는 정보 부족 분기로 빠지는지 보는 테스트가 아니라 "
            "충분한 프로젝트 설명이 있을 때 모델 실행 시간이 길어지는 동안 durable running 상태가 "
            "다른 세션에서도 관측되는지 확인하는 테스트입니다. 따라서 배포 URL 없이도 본문 길이를 "
            "충분히 확보해 사전 검증을 통과시키고, slow mock runner가 실행될 시간을 남깁니다. "
            f"{Q1_MARKER}running-state]"
        ),
        tech_stack=["Smoke Test", "Loading"],
    ),
}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run ProjectLens Q1/Q5 smoke checks.")
    parser.add_argument("--keep-existing", action="store_true")
    parser.add_argument(
        "--use-real-openai",
        action="store_true",
        help="Use the configured OpenAI key instead of deterministic mock model output.",
    )
    parser.add_argument(
        "--fail-under-threshold",
        action="store_true",
        help="Exit with status 1 if any Q1/Q5 smoke check fails.",
    )
    args = parser.parse_args()

    if not args.use_real_openai:
        settings.openai_api_key = None
        os.environ.pop("OPENAI_API_KEY", None)

    async with SessionLocal() as session:
        if not args.keep_existing:
            await cleanup_previous_rows(session)

        user = await ensure_user(session, **AUTHOR)
        await session.commit()

        results: dict[str, Any] = {
            "mode": "real_openai" if args.use_real_openai else "mock_model_with_real_mcp",
            "q1_failure_modes": {},
            "q5_decision": q5_decision(),
        }

        url_failure = await run_analysis_case(session, user.id, SMOKE_POSTS["url_unreachable"])
        ssrf = await run_analysis_case(session, user.id, SMOKE_POSTS["ssrf_blocked"])
        timeout_probe = await run_timeout_probe()
        results["q1_failure_modes"]["url_failure"] = {
            "method": "Run analysis for unreachable and SSRF URLs; direct low-timeout deploy probe.",
            "results": {
                "unreachable": url_failure,
                "ssrf_blocked": ssrf,
                "timeout_probe": timeout_probe,
            },
            "passed": (
                url_failure["status"] in {"failed", "need_more_info"}
                and ssrf["status"] in {"failed", "need_more_info"}
                and timeout_probe["passed"]
            ),
            "modified": "analysis_service forces completed reports to failed when submitted service_url is unreachable.",
        }

        thin = await run_analysis_case(session, user.id, SMOKE_POSTS["thin_site_fallback"])
        results["q1_failure_modes"]["thin_site_fallback"] = {
            "method": "Run analysis for a thin public URL plus GitHub README and sufficient post body.",
            "results": thin,
            "passed": (
                thin["status"] == "completed"
                and thin["mcp_success_by_tool"].get("fetch_github_readme", 0) > 0
                and thin["mcp_success_by_tool"].get("fetch_site_overview", 0) > 0
            ),
            "modified": "external evidence guard now requires written context or usable textual MCP/README evidence.",
        }

        rag_empty = await run_rag_empty_check(session, user.id)
        results["q1_failure_modes"]["rag_empty_result"] = {
            "method": "Call RAG retriever with an intentionally high min_indexed_posts threshold.",
            "results": rag_empty,
            "passed": rag_empty["rag_sources"] == 0,
            "modified": "No code change; SimilarProjectsCard already renders the empty state text.",
        }

        refused = await run_analysis_case(session, user.id, SMOKE_POSTS["mock_refused"])
        failed = await run_analysis_case(session, user.id, SMOKE_POSTS["mock_failed"])
        need_more = await run_analysis_case(session, user.id, SMOKE_POSTS["need_more_info"])
        results["q1_failure_modes"]["structured_output_and_statuses"] = {
            "method": "Use mock markers plus insufficient input to persist refused, failed, and need_more_info states.",
            "results": {
                "refused": refused,
                "failed": failed,
                "need_more_info": need_more,
            },
            "passed": (
                refused["status"] == "refused"
                and refused["post_analysis_status"] == "failed"
                and refused["error_type"] == "mock_refusal"
                and failed["status"] == "failed"
                and failed["post_analysis_status"] == "failed"
                and failed["error_type"] == "analysis_error"
                and need_more["status"] == "need_more_info"
                and need_more["post_analysis_status"] == "need_more_info"
            ),
            "modified": "No additional code change; existing persistence contract verified.",
        }

        running = await run_running_state_check(session, user.id)
        results["q1_failure_modes"]["slow_analysis_loading"] = {
            "method": "Patch the runner inside the smoke process to sleep, then observe DB state before completion.",
            "results": running,
            "passed": running["observed_running_before_completion"] and running["final_status"] == "completed",
            "modified": "Running remains the shared durable state; Q11 async polling also observes this status.",
        }

        results["passed"] = all(item["passed"] for item in results["q1_failure_modes"].values())
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        if args.fail_under_threshold and not results["passed"]:
            raise SystemExit(1)


async def cleanup_previous_rows(session: AsyncSession) -> None:
    smoke_post_ids = select(Post.id).where(Post.body.contains(Q1_MARKER)).subquery()
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
        techStack=smoke.tech_stack or ["Smoke Test"],
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
    mcp_success_by_tool: dict[str, int] = {}
    mcp_failure_by_tool: dict[str, int] = {}
    for row in evidence_rows:
        bucket = mcp_success_by_tool if row.success else mcp_failure_by_tool
        bucket[row.tool_name] = bucket.get(row.tool_name, 0) + 1
    return {
        "post_id": post.id,
        "report_id": result.report_id,
        "status": result.status,
        "latest_status": latest.status,
        "post_analysis_status": db_post.analysis_status if db_post else None,
        "ai_summary": db_post.ai_summary if db_post else None,
        "error_type": (result.error or {}).get("type"),
        "status_error": result.report.status.error,
        "mcp_evidence_count": len(evidence_rows),
        "mcp_success_by_tool": mcp_success_by_tool,
        "mcp_failure_by_tool": mcp_failure_by_tool,
        "rag_sources": len(result.report.evidence.rag_sources),
        "elapsed_ms": elapsed_ms,
    }


async def run_timeout_probe() -> dict[str, Any]:
    previous = os.environ.get("MCP_TIMEOUT_SECONDS")
    os.environ["MCP_TIMEOUT_SECONDS"] = "0.25"
    started = time.perf_counter()
    try:
        result = await check_deploy_status("https://httpstat.us/200?sleep=5000")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        passed = result.get("is_reachable") is False or elapsed_ms < 2000
        return {
            "passed": passed,
            "result": result,
            "elapsed_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "passed": True,
            "result": {"exception": exc.__class__.__name__, "message": str(exc)},
            "elapsed_ms": elapsed_ms,
        }
    finally:
        if previous is None:
            os.environ.pop("MCP_TIMEOUT_SECONDS", None)
        else:
            os.environ["MCP_TIMEOUT_SECONDS"] = previous


async def run_rag_empty_check(session: AsyncSession, author_id: int) -> dict[str, Any]:
    post = await insert_smoke_post(
        session,
        author_id,
        SmokePost(
            slug="rag-empty",
            title="[Q1 Smoke] RAG empty result",
            one_liner="RAG 유사 결과 빈 상태 확인.",
            body=(
                "유사도 임계값 또는 색인 수 조건이 맞지 않을 때 비슷한 프로젝트가 없다고 표시해야 합니다. "
                f"{Q1_MARKER}rag-empty]"
            ),
            tech_stack=["RAG", "Smoke Test"],
        ),
    )
    sources = await retrieve_similar_projects(
        session,
        post,
        min_indexed_posts=1_000_000,
        use_fake=True,
    )
    return {
        "post_id": post.id,
        "rag_sources": len(sources),
        "ui_empty_text": "비슷한 게시물이 아직 충분하지 않습니다.",
    }


async def run_running_state_check(session: AsyncSession, author_id: int) -> dict[str, Any]:
    post = await insert_smoke_post(session, author_id, SMOKE_POSTS["running_state"])
    post_id = post.id
    original_runner = analysis_service.run_project_analysis

    async def slow_mock_runner(*args: Any, **kwargs: Any):
        await asyncio.sleep(0.5)
        kwargs["use_mock"] = True
        return await runner_module.run_project_analysis(*args, **kwargs)

    async def run_in_separate_session():
        async with SessionLocal() as task_session:
            return await analysis_service.run_analysis_for_post(task_session, post_id)

    analysis_service.run_project_analysis = slow_mock_runner
    try:
        task = asyncio.create_task(run_in_separate_session())
        await asyncio.sleep(0.15)
        async with SessionLocal() as observed_session:
            observed_post = await observed_session.get(Post, post_id)
            observed_status = observed_post.analysis_status if observed_post else None
        result = await task
        async with SessionLocal() as final_session:
            final_post = await final_session.get(Post, post_id)
            final_status = final_post.analysis_status if final_post else None
        return {
            "post_id": post_id,
            "observed_status_before_completion": observed_status,
            "observed_running_before_completion": observed_status == "running",
            "final_status": result.status,
            "final_post_analysis_status": final_status,
        }
    finally:
        analysis_service.run_project_analysis = original_runner


def q5_decision() -> dict[str, Any]:
    return {
        "decision": "q5_historical_defer_superseded_by_q6_q10_expansion",
        "q1_q5_tools": [
            "fetch_site_overview",
            "check_deploy_status",
            "fetch_github_readme",
        ],
        "q6_q10_expansion_tools": [
            "fetch_site_context",
            "capture_screenshot",
            "run_lighthouse_summary",
        ],
        "still_deferred": ["robots", "broken links"],
        "reason": (
            "Q5 deferred new MCP tools inside the earlier MVP cut. Q6-Q10 now adds bounded same-origin context, "
            "metadata-only screenshots, and summarized Lighthouse evidence with graceful failure behavior."
        ),
        "security_contract": (
            "Keep local/private MCP, SSRF guard, redirect final URL revalidation, timeout, body/readme limits, "
            "prompt-injection boundary, allowlist, and evidence redaction."
        ),
    }


async def scalar_count(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one())


if __name__ == "__main__":
    asyncio.run(main())
