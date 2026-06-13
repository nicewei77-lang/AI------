from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas import UserCreate, UserOut, Token
from app.repositories import users as users_repo
from app.auth.security import hash_password, verify_password, create_access_token
from app.limiter import limiter
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)   
async def signup(body: UserCreate, session: AsyncSession = Depends(get_db)):
    if await users_repo.get_by_username(session, body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username taken")   
    if await users_repo.get_by_email(session, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email taken")
    hashed = hash_password(body.password)                 
    user = await users_repo.create_user(
        session, username=body.username, email=body.email, password_hash=hashed,
    )
    await session.commit()
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    user = await users_repo.get_by_username(session, form.username)       
    if user is None or not verify_password(form.password, user.password_hash):  
        raise HTTPException(status_code=401, detail="invalid credentials")  
    token = create_access_token(sub=user.username)        
    return Token(access_token=token)