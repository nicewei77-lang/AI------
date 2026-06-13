from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Vote


async def get_vote(session: AsyncSession, user_id: int, post_id: int) -> Vote | None:
    stmt = (
        select(Vote)
        .where(
            Vote.user_id == user_id,
            Vote.target_type == "post",
            Vote.target_id == post_id,
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()   # 0개 또는 1개 → 무슨 메서드?
