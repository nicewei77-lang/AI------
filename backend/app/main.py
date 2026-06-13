from fastapi import FastAPI
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router

app = FastAPI()
app.include_router(posts_router)
app.include_router(comments_router)

@app.get("/health")
async def health():
    return {"status": "ok"}