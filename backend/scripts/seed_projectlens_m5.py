from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_ROOT)
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.db import SessionLocal
from app.models import AiReport, Embedding, McpEvidence, Post, User
from app.repositories import users as users_repo
from app.schemas import PostCreate
from app.services import posts as posts_service
from app.services.analysis_service import run_analysis_for_post


M5_SEED_MARKER = "[M5_SEED:"
M5_EXTERNAL_SMOKE_MARKER = "[M5_EXTERNAL_SMOKE]"
M5_FAILURE_SMOKE_MARKER = "[M5_FAILURE_SMOKE]"


@dataclass(frozen=True)
class SeedProject:
    slug: str
    title: str
    one_liner: str
    body: str
    service_url: str
    github_url: str
    target_user: str
    tech_stack: list[str]


SEED_AUTHOR = {
    "username": "projectlens_seed_owner",
    "email": "projectlens.seed.owner@example.invalid",
    "password": "ProjectLensM5LocalOnly!234",
}

EXTERNAL_AUTHOR = {
    "username": "projectlens_external_smoke",
    "email": "projectlens.external.smoke@example.invalid",
    "password": "ProjectLensM5LocalOnly!345",
}

SEED_PROJECTS = [
    SeedProject(
        slug="projectlens",
        title="[M5 Seed] ProjectLens",
        one_liner="AI가 프로젝트 URL과 GitHub를 읽고 구조화된 진단 리포트와 유사 프로젝트를 보여주는 리뷰 게시판.",
        service_url="https://github.com/devhyun05/jungle-week15-16-302-team5-hub",
        github_url="https://github.com/devhyun05/jungle-week15-16-302-team5-hub",
        target_user="부트캠프 프로젝트를 포트폴리오와 발표 자료로 정리해야 하는 개발자",
        tech_stack=["FastAPI", "React", "PostgreSQL", "pgvector", "OpenAI Agents SDK"],
        body=(
            "ProjectLens는 기존 게시판 골격을 유지하면서 사용자가 올린 프로젝트 URL과 GitHub 저장소를 "
            "AI Agent가 분석하도록 바꾼 서비스다. Backend는 local/private MCP로 사이트와 README 근거를 "
            "수집하고, OpenAI Structured Outputs 형태의 리포트를 ai_reports에 저장한다. pgvector 기반 "
            "RAG는 쌓인 프로젝트와 분석 리포트를 검색해 비슷한 사례를 추천한다. "
            f"{M5_SEED_MARKER}projectlens]"
        ),
    ),
    SeedProject(
        slug="dom-vdom",
        title="[M5 Seed] DOM-VDOM",
        one_liner="직접 구현한 DOM/VDOM diff와 patch 과정을 눈으로 확인하는 학습형 웹 데모.",
        service_url="https://github.com/YangSiJun528/dom-vdom",
        github_url="https://github.com/YangSiJun528/dom-vdom",
        target_user="React 내부 렌더링과 DOM 패치 흐름을 코드로 이해하려는 학습자",
        tech_stack=["JavaScript", "DOM", "Virtual DOM", "Testing"],
        body=(
            "DOM-VDOM 프로젝트는 실제 DOM 조작과 가상 DOM 비교 과정을 작게 구현해 React 렌더링 개념을 "
            "실험하는 데 초점을 둔다. 사용자는 상태 변화가 어떤 diff를 만들고, patch 단계에서 브라우저 "
            "DOM이 어떻게 바뀌는지 확인할 수 있다. ProjectLens의 관점에서는 학습 목적, 구현 근거, "
            "문서화 품질을 README와 코드 구조에서 함께 볼 수 있는 좋은 시드다. "
            f"{M5_SEED_MARKER}dom-vdom]"
        ),
    ),
    SeedProject(
        slug="algoitni",
        title="[M5 Seed] Jungle AlgoItni",
        one_liner="알고리즘 학습자가 문제 풀이 흐름을 정리하고 다시 찾아볼 수 있게 돕는 학습 보조 서비스.",
        service_url="https://github.com/SISUinSea/Jungle-AlgoItni",
        github_url="https://github.com/SISUinSea/Jungle-AlgoItni",
        target_user="알고리즘 문제 풀이를 반복하며 풀이 기록과 복습 동선을 관리하려는 부트캠프 학습자",
        tech_stack=["Python", "FastAPI", "Frontend", "Algorithms"],
        body=(
            "Jungle AlgoItni는 알고리즘 학습 과정에서 문제, 풀이, 복습 포인트를 연결하려는 프로젝트다. "
            "단순 게시판보다 학습 흐름을 따라가기 쉽도록 문제 기록과 사용자 동선을 설계하는 것이 핵심이다. "
            "ProjectLens 시드로는 학습 대상 사용자, 반복 사용성, README 설명력, 실제 배포/실행 근거를 "
            "AI 리포트가 어떻게 분리해서 진단하는지 확인하는 데 쓴다. "
            f"{M5_SEED_MARKER}algoitni]"
        ),
    ),
    SeedProject(
        slug="alibai-board",
        title="[M5 Seed] ALIBAI Base Board",
        one_liner="게시글, 댓글, 투표, 인증을 갖춘 ALIBAI 게시판을 ProjectLens의 제품 골격으로 전환한 기반 프로젝트.",
        service_url="https://github.com/devhyun05/jungle-week15-16-302-team5-hub/tree/project/seungcheol-main",
        github_url="https://github.com/devhyun05/jungle-week15-16-302-team5-hub",
        target_user="프로젝트 리뷰 게시판의 기본 CRUD와 인증 흐름을 확인하려는 부트캠프 팀",
        tech_stack=["FastAPI", "React", "PostgreSQL", "JWT"],
        body=(
            "ALIBAI Base Board는 ProjectLens로 전환되기 전의 게시판 기반 프로젝트다. 게시글 작성, 댓글, "
            "투표, 로그인/JWT 인증, 태그와 검색 같은 기본 기능이 있고, 이 골격 위에 MCP evidence, Agent "
            "분석, RAG 유사 추천을 붙여 ProjectLens가 되었다. M5 시드에서는 같은 repo 안에서 제품 전환 전후의 "
            "차이를 AI 리포트와 유사 프로젝트 카드가 어떻게 보여주는지 확인한다. "
            f"{M5_SEED_MARKER}alibai-board]"
        ),
    ),
    SeedProject(
        slug="jungle-week6",
        title="[M5 Seed] Jungle Week6 Redis",
        one_liner="Redis 프로토콜과 서버 동작을 직접 구현하며 네트워크/스토리지 감각을 익히는 백엔드 프로젝트.",
        service_url="https://github.com/YangSiJun528/jungle-week6",
        github_url="https://github.com/YangSiJun528/jungle-week6",
        target_user="Redis와 TCP 서버의 내부 동작을 학습하는 시스템/백엔드 입문자",
        tech_stack=["Python", "Redis", "TCP", "pytest"],
        body=(
            "Jungle Week6 Redis 프로젝트는 Redis 명령 처리, 간단한 저장소, 네트워크 서버 흐름을 직접 구현해 "
            "백엔드 시스템의 하위 계층을 이해하려는 학습 과제다. 단순히 API만 쓰는 것이 아니라 프로토콜과 "
            "서버 라이프사이클을 만져보는 경험이 강점이다. ProjectLens 시드로는 README 근거와 본문 설명이 "
            "함께 있을 때 RAG 유사 프로젝트 추천이 어떻게 나오는지 검증한다. "
            f"{M5_SEED_MARKER}jungle-week6]"
        ),
    ),
]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed and verify ProjectLens M5 data.")
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not remove previous M5 seed/smoke posts before inserting new rows.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Insert posts only; do not run the AI analysis pipeline.",
    )
    args = parser.parse_args()

    async with SessionLocal() as session:
        if not args.keep_existing:
            await cleanup_previous_m5_rows(session)

        seed_user = await ensure_user(session, **SEED_AUTHOR)
        external_user = await ensure_user(session, **EXTERNAL_AUTHOR)
        await session.commit()

        seed_posts = []
        for seed in SEED_PROJECTS:
            post = await insert_seed_project(session, seed_user.id, seed)
            seed_posts.append(post)

        external_post = await insert_external_smoke_project(session, external_user.id)
        failure_post = await insert_failure_smoke_project(session, external_user.id)
        await session.commit()

        analysis_results: list[dict[str, Any]] = []
        if not args.skip_analysis:
            for post in [*seed_posts, external_post, failure_post]:
                result = await run_analysis_for_post(session, post.id)
                analysis_results.append(
                    {
                        "post_id": post.id,
                        "title": post.title,
                        "status": result.status,
                        "report_id": result.report_id,
                        "rag_sources": len(result.report.evidence.rag_sources),
                        "mcp_sources": len(result.report.evidence.mcp_sources),
                        "model": result.model,
                        "real_openai": not str(result.model or "").startswith("mock:"),
                    }
                )

        summary = await build_verification_summary(session, analysis_results)
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


async def cleanup_previous_m5_rows(session: AsyncSession) -> None:
    seed_post_ids = (
        select(Post.id)
        .where(
            or_(
                Post.body.contains(M5_SEED_MARKER),
                Post.body.contains(M5_EXTERNAL_SMOKE_MARKER),
                Post.body.contains(M5_FAILURE_SMOKE_MARKER),
            )
        )
        .subquery()
    )
    seed_report_ids = select(AiReport.id).where(AiReport.post_id.in_(select(seed_post_ids.c.id))).subquery()

    await session.execute(
        delete(Embedding).where(
            or_(
                (Embedding.source_type == "post")
                & (Embedding.source_id.in_(select(seed_post_ids.c.id))),
                (Embedding.source_type == "ai_report")
                & (Embedding.source_id.in_(select(seed_report_ids.c.id))),
            )
        )
    )
    await session.execute(delete(Post).where(Post.id.in_(select(seed_post_ids.c.id))))
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


async def insert_seed_project(session: AsyncSession, author_id: int, seed: SeedProject) -> Post:
    body = PostCreate(
        title=seed.title,
        body=seed.body,
        postType="project",
        serviceUrl=seed.service_url,
        githubUrl=seed.github_url,
        oneLiner=seed.one_liner,
        targetUser=seed.target_user,
        techStack=seed.tech_stack,
        tagIds=[],
    )
    return await posts_service.create(session, body, author_id=author_id)


async def insert_external_smoke_project(session: AsyncSession, author_id: int) -> Post:
    body = PostCreate(
        title="[External Smoke] URL/GitHub upload",
        body=(
            "외부 사용자가 ProjectLens에 URL과 GitHub 저장소를 제출하는 상황을 검증하기 위한 smoke 게시글이다. "
            "직접 만든 DOM/VDOM 학습 프로젝트를 예시로 올리고, 게시글 생성 이후 동일한 분석 파이프라인이 "
            "MCP evidence 저장, ai_reports 저장, RAG 유사 추천 조회까지 깨지지 않는지 확인한다. "
            f"{M5_EXTERNAL_SMOKE_MARKER}"
        ),
        postType="project",
        serviceUrl="https://github.com/YangSiJun528/dom-vdom",
        githubUrl="https://github.com/YangSiJun528/dom-vdom",
        oneLiner="외부 사용자의 URL/GitHub 업로드가 전체 분석 흐름을 통과하는지 확인하는 smoke 프로젝트.",
        targetUser="ProjectLens에 처음 프로젝트를 올리는 외부 사용자",
        techStack=["JavaScript", "ProjectLens", "Smoke Test"],
        tagIds=[],
    )
    return await posts_service.create(session, body, author_id=author_id)


async def insert_failure_smoke_project(session: AsyncSession, author_id: int) -> Post:
    body = PostCreate(
        title="[Failure Smoke] Unreachable URL",
        body=f"깨진 URL graceful 처리를 확인하는 짧은 입력. {M5_FAILURE_SMOKE_MARKER}",
        postType="project",
        serviceUrl="https://projectlens-m5-unreachable.invalid",
        githubUrl=None,
        oneLiner="접속 불가 URL이 failed 상태로 저장되는지 확인.",
        targetUser="ProjectLens 운영자",
        techStack=["Smoke Test"],
        tagIds=[],
    )
    return await posts_service.create(session, body, author_id=author_id)


async def build_verification_summary(
    session: AsyncSession,
    analysis_results: list[dict[str, Any]],
) -> dict[str, Any]:
    seed_posts_count = await scalar_count(
        session,
        select(func.count(Post.id)).where(Post.body.contains(M5_SEED_MARKER)),
    )
    completed_seed_reports = await scalar_count(
        session,
        select(func.count(AiReport.id))
        .join(Post, AiReport.post_id == Post.id)
        .where(Post.body.contains(M5_SEED_MARKER), AiReport.status == "completed"),
    )
    mcp_evidence_count = await scalar_count(
        session,
        select(func.count(McpEvidence.id))
        .join(Post, McpEvidence.post_id == Post.id)
        .where(
            or_(
                Post.body.contains(M5_SEED_MARKER),
                Post.body.contains(M5_EXTERNAL_SMOKE_MARKER),
                Post.body.contains(M5_FAILURE_SMOKE_MARKER),
            )
        ),
    )
    failed_smoke_status = (
        await session.execute(
            select(AiReport.status)
            .join(Post, AiReport.post_id == Post.id)
            .where(Post.body.contains(M5_FAILURE_SMOKE_MARKER))
            .order_by(AiReport.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    external_smoke_status = (
        await session.execute(
            select(AiReport.status)
            .join(Post, AiReport.post_id == Post.id)
            .where(Post.body.contains(M5_EXTERNAL_SMOKE_MARKER))
            .order_by(AiReport.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    rag_positive = [
        result
        for result in analysis_results
        if result["title"].startswith("[M5 Seed]") and result["rag_sources"] > 0
    ]
    mock_only = all(not result.get("real_openai") for result in analysis_results) if analysis_results else None

    return {
        "seed_posts_inserted": seed_posts_count,
        "completed_seed_reports": completed_seed_reports,
        "mcp_evidence_rows": mcp_evidence_count,
        "seed_reports_with_rag_sources": len(rag_positive),
        "external_smoke_status": external_smoke_status,
        "failure_smoke_status": failed_smoke_status,
        "openai_path": "mock_or_fake" if mock_only else "real_openai",
        "analysis_results": analysis_results,
        "ready_for_data_collection": (
            seed_posts_count == 5
            and completed_seed_reports >= 3
            and mcp_evidence_count > 0
            and len(rag_positive) > 0
            and external_smoke_status in {"completed", "need_more_info", "failed"}
            and failed_smoke_status in {"failed", "need_more_info"}
            and mock_only is False
        ),
        "note": (
            "ready_for_data_collection is false when only mock/fake OpenAI paths ran. "
            "Provide OPENAI_API_KEY and rerun before opening uploads."
        ),
    }


async def scalar_count(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one())


if __name__ == "__main__":
    asyncio.run(main())
