from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Vote


async def get_vote(
    session: AsyncSession,
    user_id: int,
    target_id: int,
    target_type: str = "post",
) -> Vote | None:
    stmt = (
        select(Vote)
        .where(
            Vote.user_id == user_id,
            Vote.target_type == target_type,
            Vote.target_id == target_id,
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()   # 0개 또는 1개 → 무슨 메서드?


async def count_votes(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: int,
    value: int | None = None,
) -> int:
    stmt = select(func.count()).select_from(Vote).where(
        Vote.target_type == target_type,
        Vote.target_id == target_id,
    )
    if value is not None:
        stmt = stmt.where(Vote.value == value)
    return int((await session.execute(stmt)).scalar_one())
