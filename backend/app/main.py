from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.config import settings
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router
from app.routers.votes import router as votes_router
from app.routers.auth import router as auth_router
from app.routers.analysis import router as analysis_router

app = FastAPI()

# rate limit 등록: 한도 초과 시 429로 응답
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(votes_router)
app.include_router(auth_router)
app.include_router(analysis_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
