# 책임: 요청에서 토큰을 꺼내 검증 → 현재 유저를 만들어 핸들러에 주입 (get_current_user 가드)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db import get_db
from app.models import User
from app.repositories import users as users_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
# 조회용: 토큰이 없어도 에러를 내지 않는다(비로그인 허용) → auto_error=False
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    user = await users_repo.get_by_username(session, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    """토큰이 있으면 유저를, 없거나 잘못됐으면 None을 반환(조회 라우트용 — 비로그인 허용)."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
    except JWTError:
        return None
    if username is None:
        return None
    return await users_repo.get_by_username(session, username)
