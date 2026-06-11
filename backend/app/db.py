from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy import text
from app.config import settings

# 연결 풀 관리자 객체인 엔진을 만든다.
engine = create_async_engine(settings.database_url, echo=True)

# 호출되면 세션을 생성하는 객체를 만든다.
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 라우터에게 세션을 빌려주고 반납하는 함수를 만든다.
async def get_db():
    async with SessionLocal() as session:
        yield session
        
# 엔진이 DB와 연결되어 쿼리가 왕복하는지 확인(연결 헬스체크)
import asyncio

async def ping():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(result.scalar())
        
if __name__ == "__main__":
    asyncio.run(ping())