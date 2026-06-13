from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Comment, Vote


async def list_comments(
    session: AsyncSession,
    post_id: int,
    user_id: int | None = None,
) -> list[Comment]:
    stmt = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.id.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()    
    comments = list(rows)
    if not comments:
        return []

    ids = [comment.id for comment in comments]
    count_stmt = (
        select(Vote.target_id, func.count())
        .where(
            Vote.target_type == "comment",
            Vote.value == 1,
            Vote.target_id.in_(ids),
        )
        .group_by(Vote.target_id)
    )
    like_counts = {
        target_id: count
        for target_id, count in (await session.execute(count_stmt)).all()
    }

    my_like_ids: set[int] = set()
    if user_id is not None:
        my_stmt = select(Vote.target_id).where(
            Vote.user_id == user_id,
            Vote.target_type == "comment",
            Vote.value == 1,
            Vote.target_id.in_(ids),
        )
        my_like_ids = set((await session.execute(my_stmt)).scalars().all())

    for comment in comments:
        comment.author_name = comment.author.username
        comment.like_count = like_counts.get(comment.id, 0)
        comment.my_like = comment.id in my_like_ids
    return comments


async def get_comment(session: AsyncSession, comment_id: int) -> Comment | None:
    stmt = select(Comment).where(Comment.id == comment_id)
    return (await session.execute(stmt)).scalar_one_or_none()


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
