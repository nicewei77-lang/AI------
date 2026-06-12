from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Post, Tag

async def get_post(session: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.tags))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_posts(
    session: AsyncSession,
    q: str | None = None,
    tag: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
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
    
    return items, next_cursor