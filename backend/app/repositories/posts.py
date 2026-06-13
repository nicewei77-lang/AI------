from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Post, Tag, Vote

async def get_post(session: AsyncSession, post_id: int, user_id: int | None = None) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.tags))
    )
    post = (await session.execute(stmt)).scalar_one_or_none()
    if post is not None:
        post.my_vote = await _my_vote(session, user_id, post_id)
    return post


async def _my_vote(session: AsyncSession, user_id: int | None, post_id: int) -> int:
    """현재 사용자가 이 글에 한 투표값(1/-1). 비로그인이거나 안 했으면 0."""
    if user_id is None:
        return 0
    stmt = select(Vote.value).where(
        Vote.user_id == user_id,
        Vote.target_type == "post",
        Vote.target_id == post_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none() or 0


async def list_posts(
    session: AsyncSession,
    q: str | None = None,
    tag: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
    user_id: int | None = None,
) -> tuple[list[Post], str | None]:
    stmt = (
        select(Post)
        .options(selectinload(Post.tags))
        .order_by(Post.id.desc())
    )
    if q:
        stmt = stmt.where(Post.title.ilike(f"%{q}%"))
    if tag:
        stmt = stmt.join(Post.tags).where(Tag.slug == tag)
    if cursor:
        stmt = stmt.where(Post.id < int(cursor))
        
    stmt = stmt.limit(limit + 1) 
    rows = (await session.execute(stmt)).scalars().all()
    has_more = len(rows) > limit # limit과 len을 비교해서 page가 더 있는지 검사
    items = rows[:limit]
    next_cursor = str(items[-1].id) if has_more else None

    # 현재 사용자의 투표를 한 번의 쿼리로 일괄 조회(N+1 방지) → 각 글에 붙임
    vote_map: dict[int, int] = {}
    if user_id is not None and items:
        ids = [p.id for p in items]
        vstmt = select(Vote.target_id, Vote.value).where(
            Vote.user_id == user_id,
            Vote.target_type == "post",
            Vote.target_id.in_(ids),
        )
        vote_map = {tid: val for tid, val in (await session.execute(vstmt)).all()}
    for p in items:
        p.my_vote = vote_map.get(p.id, 0)

    return items, next_cursor


async def create_post(
    session: AsyncSession,
    *,
    author_id: int,
    title: str,
    excuse_text: str,
    context: dict | None,
    tags: list[Tag],
) -> Post:
    post = Post(
        author_id=author_id,
        title=title,
        excuse_text=excuse_text,
        context=context,
        tags=tags
    )
    session.add(post)
    await session.flush()
    await session.refresh(post, ["created_at"])
    
    return post