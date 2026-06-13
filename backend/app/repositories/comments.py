from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Comment


async def list_comments(session: AsyncSession, post_id: int) -> list[Comment]:
    stmt = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.id.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()    
    return list(rows)


async def create_comment(
    session: AsyncSession,
    *,
    post_id: int,
    author_id: int,
    body: str,
) -> Comment:
    comment = Comment(
        post_id=post_id,                          
        author_id=author_id,                         
        body=body,
    )
    session.add(comment)
    await session.flush()                       
    await session.refresh(comment, ["created_at"])
    return comment
