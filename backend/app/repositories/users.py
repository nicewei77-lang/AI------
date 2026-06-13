from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User

async def get_by_username(session: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)     # 빈칸b: 어느 컬럼
    return (await session.execute(stmt)).scalar_one_or_none()          # 빈칸c: 0개 또는 1개 (posts.py 참고)

async def get_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()

async def create_user(session: AsyncSession, *, username: str, email: str, password_hash: str) -> User:
    user = User(username=username, email=email, password_hash=password_hash)   # 빈칸d
    session.add(user)
    await session.flush()
    await session.refresh(user, ["created_at"])
    return user
