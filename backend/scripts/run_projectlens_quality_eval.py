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
os.chdir(BACKEND_ROOT)
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.security import hash_password
from app.config import settings
from app.db import SessionLocal
from app.models import AiReport, Embedding, McpEvidence, Post, Tag, User
from app.rag.indexer import POST_SOURCE_TYPE, index_post_embedding
from app.rag.retriever import retrieve_similar_projects
from app.repositories import users as users_repo
from app.schemas import PostCreate
from app.services import posts as posts_service
from app.services.analysis_service import run_analysis_for_post


EVAL_MARKER = "[Q2_Q4_EVAL:"
INDEX_MARKER = "[Q4_INDEX_SEED:"
QUALITY_ACCEPTANCE_SCORE = 85
QUALITY_MIN_CRITERION_SCORE = 70


@dataclass(frozen=True)
class EvalProject:
    slug: str
    title: str
    service_url: str
    one_liner: str
    body: str
    target_user: str
    tech_stack: list[str]
    tag_slugs: list[str]


EVAL_AUTHOR = {
    "username": "projectlens_quality_eval",
    "email": "projectlens.quality.eval@example.invalid",
    "password": "ProjectLensQualityEvalLocalOnly!456",
}

TAG_CATALOG = {
    "portfolio": "포트폴리오",
    "frontend": "프론트엔드",
    "bootcamp": "부트캠프",
    "commerce": "커머스",
    "marketplace": "마켓플레이스",
    "mobile-web": "모바일 웹",
    "community": "커뮤니티",
    "content-feed": "콘텐츠 피드",
    "developer-tools": "개발자 도구",
    "deployment": "배포",
    "backend": "백엔드",
    "design": "디자인",
    "collaboration": "협업",
    "productivity": "생산성",
    "scheduling": "스케줄링",
    "product-discovery": "제품 탐색",
    "data-ai": "데이터/AI",
    "open-source": "오픈소스",
}

EVAL_PROJECTS = [
    EvalProject(
        slug="yeoseojin-frontend",
        title="[Q Eval] Yeoseojin Frontend Project",
        service_url="https://frontend-yeoseojin-s-projects.vercel.app/",
        one_liner="부트캠프 개인 프로젝트형 배포 사이트를 ProjectLens가 포트폴리오 관점으로 진단하는 평가 샘플.",
        target_user="부트캠프 개인 프로젝트를 포트폴리오 문장과 발표 소재로 다듬고 싶은 개발자",
        tech_stack=["Frontend", "Vercel", "Portfolio", "Bootcamp"],
        body=(
            "이 평가는 개인/부트캠프 프로젝트형 사이트에서 ProjectLens가 확인된 화면 근거와 AI 추정을 "
            "분리하고, 과장 없는 포트폴리오 문장과 발표 흐름을 생성하는지 확인한다. 사이트가 충분한 "
            "본문을 제공하지 않더라도 게시글 설명을 근거로 graceful하게 진단해야 한다. "
            f"{EVAL_MARKER}yeoseojin-frontend]"
        ),
        tag_slugs=["portfolio", "frontend", "bootcamp"],
    ),
    EvalProject(
        slug="bunjang-mobile",
        title="[Q Eval] Bunjang Mobile Commerce",
        service_url="https://m.bunjang.co.kr/",
        one_liner="상용 중고거래 서비스형 사이트에서 기능 과장 없이 확인/추정을 나누는지 보는 평가 샘플.",
        target_user="상용 서비스 UX와 핵심 흐름을 벤치마킹하려는 프로젝트 팀",
        tech_stack=["Commerce", "Mobile Web", "Marketplace", "UX"],
        body=(
            "번개장터 모바일 웹은 상용 서비스형 분석 품질을 확인하기 위한 기준 사이트다. ProjectLens는 "
            "접속 가능 여부, 페이지 메타데이터, 보이는 텍스트만 확인 사실로 다루고, 거래량이나 사용자 "
            "성과 같은 외부 근거 없는 수치를 만들어내면 안 된다. 개선 제안은 실행 가능한 제품 관점으로 "
            "제시해야 한다. "
            f"{EVAL_MARKER}bunjang-mobile]"
        ),
        tag_slugs=["commerce", "marketplace", "mobile-web"],
    ),
    EvalProject(
        slug="reddit-anime",
        title="[Q Eval] Reddit Anime Community Feed",
        service_url="https://www.reddit.com/r/anime/?screen_view_count=1",
        one_liner="커뮤니티/콘텐츠 피드형 사이트에서 fetch 실패나 본문 빈약 상황을 정직하게 처리하는 평가 샘플.",
        target_user="커뮤니티 피드와 콘텐츠 탐색 UX를 참고하려는 프로젝트 팀",
        tech_stack=["Community", "Content Feed", "Reddit", "Moderation"],
        body=(
            "Reddit anime 커뮤니티는 동적 페이지, 접근 제한, 빈약한 HTML 본문 가능성을 포함한 실패 모드 "
            "평가용 URL이다. ProjectLens는 수집 실패를 숨기지 말고, 확인 가능한 배포 상태와 게시글 설명을 "
            "구분해 분석해야 한다. RAG 결과가 약하면 유사 사례가 충분하지 않다고 말해야 한다. "
            f"{EVAL_MARKER}reddit-anime]"
        ),
        tag_slugs=["community", "content-feed"],
    ),
]

INDEX_SEED_PROJECTS = [
    EvalProject(
        slug="cal-scheduling",
        title="[Q4 Seed] Cal.com Scheduling Platform",
        service_url="https://cal.com/",
        one_liner="개인과 팀이 예약 링크, 캘린더 연동, 워크플로우로 미팅 일정을 관리하는 스케줄링 서비스.",
        target_user="예약/미팅 흐름을 자동화하려는 개인, 팀, SaaS 운영자",
        tech_stack=["Scheduling", "Calendar", "Workflow", "Open Source"],
        body=(
            "Cal.com은 예약 링크, 캘린더 연결, 가용 시간 설정, 팀 일정, 워크플로우 자동화를 중심으로 "
            "일정 예약 문제를 해결하는 공개 서비스다. ProjectLens RAG에서는 생산성/스케줄링/오픈소스 "
            "제품 사례로 쓰인다. "
            f"{INDEX_MARKER}cal-scheduling]"
        ),
        tag_slugs=["productivity", "scheduling", "open-source"],
    ),
    EvalProject(
        slug="supabase-backend",
        title="[Q4 Seed] Supabase Postgres Platform",
        service_url="https://supabase.com/",
        one_liner="Postgres 기반 데이터베이스, 인증, 스토리지, API를 제공하는 개발자용 백엔드 플랫폼.",
        target_user="빠르게 백엔드와 데이터 계층을 붙이고 싶은 앱 개발자",
        tech_stack=["Postgres", "Backend", "Auth", "Developer Tools"],
        body=(
            "Supabase는 Postgres를 중심으로 인증, 스토리지, 실시간 기능, API를 묶어 앱 백엔드를 빠르게 "
            "구성하게 해주는 개발자 도구형 서비스다. ProjectLens RAG에서는 백엔드 플랫폼과 개발자 도구 "
            "사례로 색인한다. "
            f"{INDEX_MARKER}supabase-backend]"
        ),
        tag_slugs=["backend", "developer-tools", "open-source"],
    ),
    EvalProject(
        slug="linear-product-dev",
        title="[Q4 Seed] Linear Product Development",
        service_url="https://linear.app/",
        one_liner="제품 팀이 이슈, 로드맵, 프로젝트 실행을 관리하는 제품 개발 운영 도구.",
        target_user="개발/제품 이슈를 빠르게 정리하고 실행 흐름을 맞추려는 팀",
        tech_stack=["Product Management", "Issue Tracking", "Collaboration"],
        body=(
            "Linear는 이슈 관리, 프로젝트, 로드맵, 팀 협업 흐름을 제품 개발 중심으로 정리하는 SaaS다. "
            "ProjectLens RAG에서는 협업/생산성/제품 운영 사례로 쓰인다. "
            f"{INDEX_MARKER}linear-product-dev]"
        ),
        tag_slugs=["productivity", "collaboration", "developer-tools"],
    ),
    EvalProject(
        slug="figma-design-collaboration",
        title="[Q4 Seed] Figma Design Collaboration",
        service_url="https://www.figma.com/",
        one_liner="팀이 인터페이스 디자인, 프로토타입, 디자인 시스템을 함께 만드는 협업 디자인 도구.",
        target_user="디자인과 개발 협업을 하나의 캔버스에서 관리하려는 제품 팀",
        tech_stack=["Design", "Prototype", "Collaboration"],
        body=(
            "Figma는 인터페이스 디자인, 프로토타입, 디자인 시스템, 팀 협업을 웹 기반으로 제공하는 제품이다. "
            "ProjectLens RAG에서는 디자인 협업/프로토타이핑 사례로 색인한다. "
            f"{INDEX_MARKER}figma-design-collaboration]"
        ),
        tag_slugs=["design", "collaboration", "productivity"],
    ),
    EvalProject(
        slug="vercel-deployment",
        title="[Q4 Seed] Vercel Deployment Platform",
        service_url="https://vercel.com/",
        one_liner="프론트엔드와 풀스택 웹 앱을 빌드, 배포, 운영하는 개발자 플랫폼.",
        target_user="Next.js/프론트엔드 프로젝트를 빠르게 배포하고 운영하려는 개발자",
        tech_stack=["Deployment", "Frontend", "Next.js", "Developer Tools"],
        body=(
            "Vercel은 프론트엔드와 풀스택 웹 앱의 빌드, 프리뷰, 배포, 운영을 돕는 개발자 플랫폼이다. "
            "ProjectLens RAG에서는 배포/프론트엔드/개발자 도구 사례로 사용한다. "
            f"{INDEX_MARKER}vercel-deployment]"
        ),
        tag_slugs=["deployment", "frontend", "developer-tools"],
    ),
    EvalProject(
        slug="dev-community",
        title="[Q4 Seed] DEV Community Content Feed",
        service_url="https://dev.to/",
        one_liner="개발자가 글, 토론, 태그 기반 피드를 통해 지식을 공유하는 커뮤니티 플랫폼.",
        target_user="기술 콘텐츠를 탐색하고 글을 공유하려는 개발자 커뮤니티",
        tech_stack=["Community", "Content Feed", "Tags", "Publishing"],
        body=(
            "DEV Community는 개발자들이 글을 쓰고 태그 기반으로 탐색하며 토론하는 콘텐츠 피드형 커뮤니티다. "
            "ProjectLens RAG에서는 커뮤니티/콘텐츠 피드/태그 탐색 사례로 색인한다. "
            f"{INDEX_MARKER}dev-community]"
        ),
        tag_slugs=["community", "content-feed", "developer-tools"],
    ),
    EvalProject(
        slug="hacker-news-feed",
        title="[Q4 Seed] Hacker News Link Feed",
        service_url="https://news.ycombinator.com/",
        one_liner="사용자가 링크와 토론을 올리고 점수 기반으로 읽는 개발자/스타트업 뉴스 피드.",
        target_user="기술 뉴스와 토론을 빠르게 훑고 싶은 개발자와 창업자",
        tech_stack=["Community", "Link Feed", "Voting"],
        body=(
            "Hacker News는 링크 제출, 댓글, 투표를 중심으로 스타트업/기술 뉴스를 정렬하는 커뮤니티 피드다. "
            "ProjectLens RAG에서는 콘텐츠 피드와 투표 기반 커뮤니티 사례로 쓴다. "
            f"{INDEX_MARKER}hacker-news-feed]"
        ),
        tag_slugs=["community", "content-feed"],
    ),
    EvalProject(
        slug="etsy-marketplace",
        title="[Q4 Seed] Etsy Handmade Marketplace",
        service_url="https://www.etsy.com/",
        one_liner="핸드메이드, 빈티지, 커스텀 상품을 탐색하고 구매하는 창작자 중심 마켓플레이스.",
        target_user="개성 있는 상품을 찾는 구매자와 독립 창작자/판매자",
        tech_stack=["Commerce", "Marketplace", "Search", "Seller Tools"],
        body=(
            "Etsy는 독립 판매자와 구매자를 연결하고 상품 탐색, 검색, 결제 흐름을 제공하는 커머스 "
            "마켓플레이스다. ProjectLens RAG에서는 거래/탐색/판매자 도구 사례로 색인한다. "
            f"{INDEX_MARKER}etsy-marketplace]"
        ),
        tag_slugs=["commerce", "marketplace"],
    ),
    EvalProject(
        slug="product-hunt-discovery",
        title="[Q4 Seed] Product Hunt Discovery Feed",
        service_url="https://www.producthunt.com/",
        one_liner="새로운 기술 제품을 공개하고 순위, 댓글, 커뮤니티 반응으로 발견하는 제품 탐색 피드.",
        target_user="새 제품을 찾거나 초기 사용자 반응을 얻고 싶은 메이커와 얼리어답터",
        tech_stack=["Product Discovery", "Community", "Launch", "Voting"],
        body=(
            "Product Hunt는 새 제품 런칭, 커뮤니티 투표, 댓글, 순위 기반 발견을 중심으로 하는 제품 탐색 "
            "플랫폼이다. ProjectLens RAG에서는 제품 공개/커뮤니티 피드 사례로 사용한다. "
            f"{INDEX_MARKER}product-hunt-discovery]"
        ),
        tag_slugs=["product-discovery", "community", "content-feed"],
    ),
    EvalProject(
        slug="behance-portfolio",
        title="[Q4 Seed] Behance Creative Portfolio",
        service_url="https://www.behance.net/",
        one_liner="크리에이터가 프로젝트 작업물을 공개하고 탐색, 채용, 영감을 얻는 포트폴리오 플랫폼.",
        target_user="작업물을 공개하고 피드백/채용 기회를 얻고 싶은 디자이너와 창작자",
        tech_stack=["Portfolio", "Design", "Creative Community"],
        body=(
            "Behance는 창작자가 프로젝트 작업물을 포트폴리오 형태로 공개하고, 탐색/추천/채용 맥락으로 "
            "연결되는 크리에이티브 커뮤니티다. ProjectLens RAG에서는 포트폴리오/디자인/커뮤니티 사례로 "
            "색인한다. "
            f"{INDEX_MARKER}behance-portfolio]"
        ),
        tag_slugs=["portfolio", "design", "community"],
    ),
]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run ProjectLens Q2-Q4 quality evals.")
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not remove previous Q eval posts before inserting new rows.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Insert/index eval posts but do not run the AI analysis pipeline.",
    )
    parser.add_argument(
        "--use-fake-embeddings",
        action="store_true",
        help="Force deterministic local fake embeddings for post backfill.",
    )
    parser.add_argument(
        "--backfill-all-posts",
        action="store_true",
        help=(
            "Refresh embeddings for every local post. This can send non-eval post "
            "content to the embedding API, so the default is eval posts only."
        ),
    )
    parser.add_argument(
        "--skip-index-seeds",
        action="store_true",
        help="Do not insert/index the public Q4 seed projects.",
    )
    parser.add_argument(
        "--min-quality-score",
        type=int,
        default=QUALITY_ACCEPTANCE_SCORE,
        help="Per-eval overall rubric score required for the quality gate.",
    )
    parser.add_argument(
        "--min-criterion-score",
        type=int,
        default=QUALITY_MIN_CRITERION_SCORE,
        help="Per-criterion percentage required for the quality gate.",
    )
    parser.add_argument(
        "--fail-under-threshold",
        action="store_true",
        help="Exit with status 1 when any eval misses the rubric quality gate.",
    )
    args = parser.parse_args()

    async with SessionLocal() as session:
        if not args.keep_existing:
            await cleanup_previous_eval_rows(session)

        await ensure_tags(session)
        eval_user = await ensure_user(session, **EVAL_AUTHOR)
        await session.commit()

        seed_posts = []
        if not args.skip_index_seeds:
            seed_posts = await ensure_index_seed_projects(session, eval_user.id)
            await session.commit()

        eval_posts = []
        for item in EVAL_PROJECTS:
            eval_posts.append(await insert_eval_project(session, eval_user.id, item))
        await session.commit()

        scoped_post_ids = [post.id for post in seed_posts + eval_posts]
        backfill_summary = await backfill_post_embeddings(
            session,
            post_ids=None if args.backfill_all_posts else scoped_post_ids,
            use_fake=args.use_fake_embeddings,
        )
        await session.commit()

        analysis_results: list[dict[str, Any]] = []
        if not args.skip_analysis:
            for post in eval_posts:
                started = time.perf_counter()
                result = await run_analysis_for_post(session, post.id)
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                expansion_metrics = await collect_mcp_expansion_metrics(
                    session,
                    post.id,
                    elapsed_ms=elapsed_ms,
                )
                analysis_results.append(
                    {
                        "slug": _slug_for_post(post),
                        "post_id": post.id,
                        "title": post.title,
                        "status": result.status,
                        "report_id": result.report_id,
                        "model": result.model,
                        "real_openai": not str(result.model or "").startswith("mock:"),
                        "mcp_sources": len(result.report.evidence.mcp_sources),
                        "rag_sources": len(result.report.evidence.rag_sources),
                        **expansion_metrics,
                        "confirmed_facts": len(result.report.service_understanding.confirmed_facts),
                        "inferred_facts": len(result.report.service_understanding.inferred_facts),
                        "weaknesses": len(result.report.diagnosis.weaknesses),
                        "portfolio_ready": bool(result.report.portfolio.headline.strip()),
                        "presentation_ready": bool(result.report.presentation.opening.strip()),
                        "quality_rubric": score_quality_rubric(
                            result.report.model_dump(mode="json"),
                            min_quality_score=args.min_quality_score,
                            min_criterion_score=args.min_criterion_score,
                        ),
                        "gaps": quality_gaps(result.report.model_dump(mode="json")),
                    }
                )

        comparison = await compare_rag_modes(session)
        summary = await build_summary(
            session,
            backfill_summary,
            analysis_results,
            comparison,
            seed_posts=seed_posts,
            min_quality_score=args.min_quality_score,
            min_criterion_score=args.min_criterion_score,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        if args.fail_under_threshold and not summary["quality_gate_passed"]:
            raise SystemExit(1)


async def cleanup_previous_eval_rows(session: AsyncSession) -> None:
    eval_post_ids = select(Post.id).where(Post.body.contains(EVAL_MARKER)).subquery()
    eval_report_ids = select(AiReport.id).where(AiReport.post_id.in_(select(eval_post_ids.c.id))).subquery()

    await session.execute(
        delete(Embedding).where(
            or_(
                (Embedding.source_type == "post")
                & (Embedding.source_id.in_(select(eval_post_ids.c.id))),
                (Embedding.source_type == "ai_report")
                & (Embedding.source_id.in_(select(eval_report_ids.c.id))),
            )
        )
    )
    await session.execute(delete(Post).where(Post.id.in_(select(eval_post_ids.c.id))))
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


async def ensure_tags(session: AsyncSession) -> None:
    stmt = select(Tag).where(Tag.slug.in_(TAG_CATALOG.keys()))
    existing = {tag.slug for tag in (await session.execute(stmt)).scalars().all()}
    for slug, name in TAG_CATALOG.items():
        if slug not in existing:
            session.add(Tag(slug=slug, name=name))
    await session.flush()


async def ensure_index_seed_projects(session: AsyncSession, author_id: int) -> list[Post]:
    posts: list[Post] = []
    for item in INDEX_SEED_PROJECTS:
        existing = await _find_project_by_marker(session, INDEX_MARKER, item.slug)
        if existing is None:
            posts.append(await insert_eval_project(session, author_id, item))
            continue

        existing.title = item.title
        existing.body = item.body
        existing.post_type = "project"
        existing.service_url = item.service_url
        existing.github_url = None
        existing.one_liner = item.one_liner
        existing.target_user = item.target_user
        existing.tech_stack = item.tech_stack
        existing.tags = await _load_tags(session, item.tag_slugs)
        posts.append(existing)

    await session.flush()
    return posts


async def insert_eval_project(session: AsyncSession, author_id: int, item: EvalProject) -> Post:
    body = PostCreate(
        title=item.title,
        body=item.body,
        postType="project",
        serviceUrl=item.service_url,
        githubUrl=None,
        oneLiner=item.one_liner,
        targetUser=item.target_user,
        techStack=item.tech_stack,
        tagIds=item.tag_slugs,
    )
    return await posts_service.create(session, body, author_id=author_id)


async def _find_project_by_marker(session: AsyncSession, marker: str, slug: str) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.body.contains(f"{marker}{slug}]"))
        .options(selectinload(Post.tags))
        .order_by(Post.id.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _load_tags(session: AsyncSession, slugs: list[str]) -> list[Tag]:
    if not slugs:
        return []
    stmt = select(Tag).where(Tag.slug.in_(slugs))
    tags = list((await session.execute(stmt)).scalars().all())
    found = {tag.slug for tag in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"missing seed tags: {sorted(missing)}")
    tags_by_slug = {tag.slug: tag for tag in tags}
    return [tags_by_slug[slug] for slug in slugs]



async def backfill_post_embeddings(
    session: AsyncSession,
    *,
    post_ids: list[int] | None,
    use_fake: bool,
) -> dict[str, int]:
    stmt = select(Post).options(selectinload(Post.tags)).order_by(Post.id)
    if post_ids is not None:
        stmt = stmt.where(Post.id.in_(post_ids))
    posts = list((await session.execute(stmt)).scalars().all())
    existing_rows = (
        await session.execute(select(Embedding).where(Embedding.source_type == POST_SOURCE_TYPE))
    ).scalars().all()
    existing_by_post_id = {row.source_id: row for row in existing_rows}

    indexed = 0
    skipped = 0
    for post in posts:
        existing = existing_by_post_id.get(post.id)
        if existing is not None and not _should_refresh_embedding(existing):
            skipped += 1
            continue
        await index_post_embedding(
            session,
            post,
            use_fake=True if use_fake else None,
        )
        indexed += 1

    return {
        "scope": "all_posts" if post_ids is None else "public_index_seed_and_eval_posts",
        "posts_seen": len(posts),
        "indexed_or_refreshed": indexed,
        "skipped": skipped,
    }


def _should_refresh_embedding(row: Embedding) -> bool:
    if not row.embedding_model or row.embedding_model.startswith("fake:"):
        return True
    metadata = row.metadata_ or {}
    return bool(metadata.get("fake_embedding"))


async def compare_rag_modes(session: AsyncSession) -> list[dict[str, Any]]:
    stmt = (
        select(Post)
        .where(Post.body.contains(EVAL_MARKER))
        .options(selectinload(Post.tags))
        .order_by(Post.id)
    )
    posts = list((await session.execute(stmt)).scalars().all())
    rows = []
    for post in posts:
        cosine = await retrieve_similar_projects(session, post, ranking_mode="cosine")
        weighted = await retrieve_similar_projects(session, post, ranking_mode="weighted")
        rows.append(
            {
                "slug": _slug_for_post(post),
                "post_id": post.id,
                "cosine": [source.model_dump(mode="json") for source in cosine],
                "weighted": [source.model_dump(mode="json") for source in weighted],
            }
        )
    return rows


async def collect_mcp_expansion_metrics(
    session: AsyncSession,
    post_id: int,
    *,
    elapsed_ms: int,
) -> dict[str, Any]:
    rows = list(
        (
            await session.execute(
                select(McpEvidence)
                .where(McpEvidence.post_id == post_id)
                .order_by(McpEvidence.id)
            )
        )
        .scalars()
        .all()
    )
    site_context_pages = 0
    screenshot_captured = False
    lighthouse_scores_present = False
    success_by_tool: dict[str, int] = {}
    failure_by_tool: dict[str, int] = {}
    for row in rows:
        bucket = success_by_tool if row.success else failure_by_tool
        bucket[row.tool_name] = bucket.get(row.tool_name, 0) + 1
        result = row.result if isinstance(row.result, dict) else {}
        if row.tool_name == "fetch_site_context" and row.success:
            pages = result.get("pages")
            if isinstance(pages, list):
                site_context_pages = max(site_context_pages, len(pages))
        elif row.tool_name == "capture_screenshot" and row.success:
            screenshot_captured = bool(result.get("screenshot_saved"))
        elif row.tool_name == "run_lighthouse_summary" and row.success:
            scores = result.get("scores")
            lighthouse_scores_present = isinstance(scores, dict) and any(
                isinstance(value, (int, float)) for value in scores.values()
            )
    return {
        "site_context_pages": site_context_pages,
        "screenshot_captured": screenshot_captured,
        "lighthouse_scores_present": lighthouse_scores_present,
        "analysis_elapsed_ms": elapsed_ms,
        "mcp_success_by_tool": success_by_tool,
        "mcp_failure_by_tool": failure_by_tool,
    }


async def build_summary(
    session: AsyncSession,
    backfill_summary: dict[str, int],
    analysis_results: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    *,
    seed_posts: list[Post],
    min_quality_score: int,
    min_criterion_score: int,
) -> dict[str, Any]:
    post_count = await scalar_count(session, select(func.count(Post.id)))
    post_embedding_count = await scalar_count(
        session,
        select(func.count(Embedding.id)).where(Embedding.source_type == POST_SOURCE_TYPE),
    )
    eval_report_count = await scalar_count(
        session,
        select(func.count(AiReport.id))
        .join(Post, AiReport.post_id == Post.id)
        .where(Post.body.contains(EVAL_MARKER)),
    )
    eval_mcp_count = await scalar_count(
        session,
        select(func.count(McpEvidence.id))
        .join(Post, McpEvidence.post_id == Post.id)
        .where(Post.body.contains(EVAL_MARKER)),
    )

    quality_gate_passed = bool(analysis_results) and all(
        result["quality_rubric"]["passed"] for result in analysis_results
    )
    elapsed_values = [
        int(result["analysis_elapsed_ms"])
        for result in analysis_results
        if isinstance(result.get("analysis_elapsed_ms"), int)
    ]

    return {
        "openai_api_key_present": bool(settings.openai_api_key),
        "agent_model": settings.agent_model,
        "post_count": post_count,
        "post_embedding_count": post_embedding_count,
        "q4_data_sufficient_for_weighted": post_embedding_count >= settings.rag_weighted_min_indexed_posts,
        "rag_weighted_min_indexed_posts": settings.rag_weighted_min_indexed_posts,
        "q4_index_seed_count": len(seed_posts),
        "quality_gate": {
            "min_quality_score": min_quality_score,
            "min_criterion_score": min_criterion_score,
        },
        "quality_gate_passed": quality_gate_passed,
        "backfill": backfill_summary,
        "eval_report_count": eval_report_count,
        "eval_mcp_evidence_count": eval_mcp_count,
        "q11_latency": {
            "analysis_elapsed_ms": elapsed_values,
            "over_15s_count": sum(1 for value in elapsed_values if value > 15_000),
            "async_jobs_deferred": sum(1 for value in elapsed_values if value > 15_000) < 2,
        },
        "analysis_results": analysis_results,
        "rag_mode_comparison": comparison,
    }


def quality_gaps(report: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    status = report.get("status", {}).get("status")
    if status != "completed":
        gaps.append(f"status={status}")
    service = report.get("service_understanding", {})
    if not service.get("confirmed_facts"):
        gaps.append("confirmed_facts empty")
    if not service.get("inferred_facts"):
        gaps.append("inferred_facts empty")
    evidence = report.get("evidence", {})
    if not evidence.get("mcp_sources"):
        gaps.append("mcp_sources empty")
    portfolio = report.get("portfolio", {})
    if not portfolio.get("headline"):
        gaps.append("portfolio headline empty")
    presentation = report.get("presentation", {})
    if not presentation.get("opening"):
        gaps.append("presentation opening empty")
    return gaps


def score_quality_rubric(
    report: dict[str, Any],
    *,
    min_quality_score: int,
    min_criterion_score: int,
) -> dict[str, Any]:
    phases = {
        "q2_prompt_schema": _phase_score(
            "q2_prompt_schema",
            [
                _score_evidence_grounding(report),
                _score_uncertainty_control(report),
                _score_service_insight(report),
                _score_actionability(report),
            ],
        ),
        "q3_portfolio_presentation": _phase_score(
            "q3_portfolio_presentation",
            [_score_q3_portfolio_presentation(report)],
        ),
        "q4_weighted_rag": _phase_score(
            "q4_weighted_rag",
            [_score_q4_rag(report)],
        ),
    }
    total = round(sum(phase["score"] for phase in phases.values()) / len(phases))
    weak_criteria = []
    for phase in phases.values():
        for criterion in phase["criteria"]:
            if criterion["percent"] < min_criterion_score:
                weak_criteria.append(f"{phase['name']}:{criterion['name']}")
    weak_phases = [
        phase["name"]
        for phase in phases.values()
        if phase["score"] < min_quality_score
    ]
    passed = total >= min_quality_score and not weak_criteria and not weak_phases
    return {
        "total_score": total,
        "max_score": 100,
        "passed": passed,
        "weak_phases": weak_phases,
        "weak_criteria": weak_criteria,
        "phases": phases,
    }


def _score_evidence_grounding(report: dict[str, Any]) -> dict[str, Any]:
    service = report.get("service_understanding", {})
    evidence = report.get("evidence", {})
    diagnosis = report.get("diagnosis", {})
    portfolio = report.get("portfolio", {})
    mcp_sources = evidence.get("mcp_sources") or []
    confirmed_facts = _clean_list(service.get("confirmed_facts"))
    proof_points = _clean_list(portfolio.get("proof_points"))
    diagnostic_items = [
        *(diagnosis.get("strengths") or []),
        *(diagnosis.get("weaknesses") or []),
    ]

    score = 0
    notes: list[str] = []
    score += _points(report.get("status", {}).get("status") == "completed", 3, notes, "completed status")
    score += min(5, len(mcp_sources) * 3)
    if len(mcp_sources) < 2:
        notes.append("needs at least 2 MCP/deploy evidence sources")
    score += min(5, len(confirmed_facts))
    if len(confirmed_facts) < 4:
        notes.append("needs 4+ confirmed facts")
    if diagnostic_items and all(_has_evidence_fields(item) for item in diagnostic_items):
        score += 4
    else:
        notes.append("diagnosis items need evidence/confidence fields")
    score += min(3, len(proof_points) * 2)
    if len(proof_points) < 2:
        notes.append("portfolio needs 2+ proof points")
    return _criterion("evidence_grounding", score, 20, notes)


def _score_uncertainty_control(report: dict[str, Any]) -> dict[str, Any]:
    service = report.get("service_understanding", {})
    portfolio = report.get("portfolio", {})
    text_blob = json.dumps(report, ensure_ascii=False)
    confirmed_facts = _clean_list(service.get("confirmed_facts"))
    inferred_facts = _clean_list(service.get("inferred_facts"))
    limitations = _clean_list(portfolio.get("limitations"))
    uncertainty_terms = ("추정", "확인", "근거", "부족", "제한", "보이지", "알 수")
    overclaim_terms = ("세계 최고", "압도적", "100만", "매출", "트래픽", "반드시 성공", "확실히 성장")

    score = 0
    notes: list[str] = []
    score += _points(bool(confirmed_facts and inferred_facts), 5, notes, "confirmed/inferred split")
    score += _points(1 <= len(inferred_facts) <= 4, 3, notes, "bounded inferred facts")
    score += min(5, len(limitations) * 5)
    if not limitations:
        notes.append("portfolio limitations missing")
    score += _points(any(term in text_blob for term in uncertainty_terms), 3, notes, "uncertainty language")
    score += _points(not any(term in text_blob for term in overclaim_terms), 4, notes, "no obvious overclaim terms")
    return _criterion("uncertainty_control", score, 20, notes)


def _score_actionability(report: dict[str, Any]) -> dict[str, Any]:
    diagnosis = report.get("diagnosis", {})
    strengths = diagnosis.get("strengths") or []
    weaknesses = diagnosis.get("weaknesses") or []
    improvements = diagnosis.get("improvement_plan") or []
    score = 0
    notes: list[str] = []

    score += min(4, len(strengths) * 2)
    if len(strengths) < 2:
        notes.append("needs 2+ strengths")
    score += min(5, len(weaknesses) * 2)
    if len(weaknesses) < 3:
        notes.append("needs 3+ weaknesses")
    score += min(5, len(improvements) * 2)
    if len(improvements) < 3:
        notes.append("needs 3+ improvement actions")
    score += _points(any(item.get("priority") == "P0" for item in improvements), 3, notes, "P0 action")
    if improvements and all(_useful_action(item) for item in improvements):
        score += 3
    else:
        notes.append("improvement actions need action and expected effect")
    return _criterion("actionability", score, 20, notes)


def _score_portfolio_presentation(report: dict[str, Any]) -> dict[str, Any]:
    portfolio = report.get("portfolio", {})
    presentation = report.get("presentation", {})
    score = 0
    notes: list[str] = []
    core_fields = [
        portfolio.get("headline"),
        portfolio.get("problem"),
        portfolio.get("solution"),
        portfolio.get("impact"),
    ]
    score += min(8, _nonempty_count(core_fields) * 2)
    if _nonempty_count(core_fields) < 4:
        notes.append("portfolio headline/problem/solution/impact incomplete")

    support_lists = [
        _clean_list(portfolio.get("tech_highlights")),
        _clean_list(portfolio.get("proof_points")),
        _clean_list(portfolio.get("limitations")),
    ]
    score += _points(all(support_lists), 5, notes, "portfolio support lists")

    presentation_fields = [
        presentation.get("opening"),
        presentation.get("closing"),
    ]
    has_presentation_lists = (
        len(_clean_list(presentation.get("key_points"))) >= 2
        and len(_clean_list(presentation.get("demo_flow"))) >= 2
    )
    score += _points(_nonempty_count(presentation_fields) == 2 and has_presentation_lists, 7, notes, "presentation coverage")
    return _criterion("portfolio_presentation", score, 20, notes)


def _score_service_insight(report: dict[str, Any]) -> dict[str, Any]:
    service = report.get("service_understanding", {})
    site_structure = str(service.get("site_structure_summary") or "").strip()
    service_essence = str(service.get("service_essence") or "").strip()
    key_insight = str(service.get("key_insight") or "").strip()
    summary_text = " ".join(
        str(service.get(key) or "")
        for key in ("one_line_summary", "detailed_summary", "site_structure_summary", "service_essence", "key_insight")
    )
    structure_terms = (
        "title",
        "h1",
        "메타",
        "본문",
        "main",
        "링크",
        "네비",
        "페이지",
        "구조",
        "피드",
        "검색",
        "CTA",
        "검증",
        "verification",
        "접근",
        "배포",
    )
    insight_terms = (
        "UX",
        "포지셔닝",
        "구조",
        "리스크",
        "한계",
        "흐름",
        "전환",
        "탐색",
        "신뢰",
        "발표",
        "포트폴리오",
    )
    notes: list[str] = []
    score = 0
    score += _points(
        bool(site_structure and service_essence and key_insight),
        12,
        notes,
        "site structure, service essence, and key insight fields",
    )
    score += _points(
        any(term in site_structure for term in structure_terms),
        8,
        notes,
        "visible website structure signals",
    )
    score += _points(
        len(service_essence) >= 35 and any(term in service_essence for term in ("서비스", "제품", "플랫폼", "커뮤니티", "마켓", "프로젝트", "피드")),
        8,
        notes,
        "specific service essence",
    )
    score += _points(
        len(key_insight) >= 45 and any(term in key_insight for term in insight_terms),
        8,
        notes,
        "actionable service insight",
    )
    score += _points(
        "평가 샘플" not in str(service.get("one_line_summary") or ""),
        4,
        notes,
        "one-line summary should not center the eval framing",
    )
    if summary_text.count("평가 샘플") > 2:
        notes.append("report over-centers eval framing instead of service essence")
        score = max(0, score - 6)
    return _criterion("service_structure_and_insight", score, 40, notes)


def _score_q3_portfolio_presentation(report: dict[str, Any]) -> dict[str, Any]:
    portfolio = report.get("portfolio", {})
    presentation = report.get("presentation", {})
    service = report.get("service_understanding", {})
    text_blob = " ".join(
        [
            str(portfolio.get("headline") or ""),
            str(portfolio.get("problem") or ""),
            str(portfolio.get("solution") or ""),
            str(portfolio.get("impact") or ""),
            str(presentation.get("opening") or ""),
            str(presentation.get("closing") or ""),
            " ".join(_clean_list(presentation.get("key_points"))),
            " ".join(_clean_list(presentation.get("demo_flow"))),
        ]
    )
    notes: list[str] = []
    score = 0
    score += min(
        20,
        _nonempty_count(
            [
                portfolio.get("headline"),
                portfolio.get("problem"),
                portfolio.get("solution"),
                portfolio.get("impact"),
            ]
        )
        * 5,
    )
    if _nonempty_count([portfolio.get("headline"), portfolio.get("problem"), portfolio.get("solution"), portfolio.get("impact")]) < 4:
        notes.append("portfolio headline/problem/solution/impact incomplete")
    score += _points(len(_clean_list(portfolio.get("proof_points"))) >= 2, 15, notes, "2+ portfolio proof points")
    score += _points(len(_clean_list(portfolio.get("limitations"))) >= 1, 10, notes, "portfolio limitation")
    score += _points(len(_clean_list(portfolio.get("tech_highlights"))) >= 2, 10, notes, "2+ tech highlights")
    score += _points(bool(str(presentation.get("opening") or "").strip()), 10, notes, "presentation opening")
    score += _points(len(_clean_list(presentation.get("key_points"))) >= 2, 10, notes, "2+ presentation key points")
    score += _points(len(_clean_list(presentation.get("demo_flow"))) >= 2, 10, notes, "2+ demo flow steps")
    score += _points(bool(str(presentation.get("closing") or "").strip()), 5, notes, "presentation closing")
    score += _points(
        any(
            term
            for term in (
                str(service.get("service_essence") or "")[:16],
                str(service.get("key_insight") or "")[:16],
                "근거",
                "한계",
                "확인",
            )
            if term and term in text_blob
        ),
        10,
        notes,
        "copy should reuse service essence, evidence, or limitations",
    )
    return _criterion("q3_portfolio_presentation_quality", score, 100, notes)


def _score_q4_rag(report: dict[str, Any]) -> dict[str, Any]:
    rag_sources = report.get("evidence", {}).get("rag_sources") or []
    score = 0
    notes: list[str] = []
    score += min(20, len(rag_sources) * 7)
    if len(rag_sources) < 3:
        notes.append("needs 3 RAG sources")
    score += _points(
        bool(rag_sources) and all(source.get("ranking_mode") == "weighted" for source in rag_sources),
        25,
        notes,
        "weighted ranking mode",
    )
    score += _points(
        bool(rag_sources) and all(source.get("score_breakdown") for source in rag_sources),
        20,
        notes,
        "weighted score breakdown",
    )
    score += _points(
        bool(rag_sources) and all(_clean_list(source.get("match_reasons")) for source in rag_sources),
        20,
        notes,
        "match reasons",
    )
    reason_blob = " ".join(
        reason
        for source in rag_sources
        for reason in _clean_list(source.get("match_reasons"))
    )
    score += _points(
        any(term in reason_blob for term in ("겹치는 태그", "같은 게시물 유형", "최근", "반응 점수")),
        15,
        notes,
        "non-semantic weighted signal",
    )
    return _criterion("q4_weighted_rag_quality", score, 100, notes)


def _phase_score(name: str, criteria: list[dict[str, Any]]) -> dict[str, Any]:
    score = sum(item["score"] for item in criteria)
    max_score = sum(item["max_score"] for item in criteria)
    percent = round(score / max_score * 100) if max_score else 0
    return {
        "name": name,
        "score": percent,
        "raw_score": score,
        "max_score": max_score,
        "criteria": criteria,
    }


def _criterion(name: str, score: int, max_score: int, notes: list[str]) -> dict[str, Any]:
    bounded = max(0, min(score, max_score))
    return {
        "name": name,
        "score": bounded,
        "max_score": max_score,
        "percent": round(bounded / max_score * 100) if max_score else 0,
        "notes": notes,
    }


def _points(condition: bool, value: int, notes: list[str], note: str) -> int:
    if condition:
        return value
    notes.append(f"missing {note}")
    return 0


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _nonempty_count(values: list[Any]) -> int:
    return sum(1 for value in values if str(value or "").strip())


def _has_evidence_fields(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return bool(item.get("evidence_kind") and item.get("based_on") and item.get("confidence"))


def _useful_action(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return len(str(item.get("action") or "").strip()) >= 12 and len(
        str(item.get("expected_effect") or "").strip()
    ) >= 12


def _slug_for_post(post: Post) -> str:
    for item in EVAL_PROJECTS:
        if f"{EVAL_MARKER}{item.slug}]" in (post.body or ""):
            return item.slug
    return str(post.id)


async def scalar_count(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one())


if __name__ == "__main__":
    asyncio.run(main())
