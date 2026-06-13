# 책임: 비밀번호 해싱/검증, JWT 토큰 생성/디코드 (순수 함수 모음 — DB·요청 모름)
from passlib.context import CryptContext

# bcrypt 컨텍스트: 어떤 알고리즘으로 해싱할지 지정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")   # 빈칸1: 알고리즘 이름

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)             # 빈칸2: 평문 → 해시 한 줄로

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)     # 빈칸3: 평문이 해시와 맞는지 (bool 반환)


from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

def create_access_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=50)   # 빈칸1: 만료까지 몇 분 (예: 60)
    payload = {
        "sub": sub,                       # 빈칸2: 누구의 토큰인가 (인자로 받은 값)
        "exp": expire,                       # 빈칸3: 만료시각 (위에서 만든 변수)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")  # 빈칸4: 서명 알고리즘
