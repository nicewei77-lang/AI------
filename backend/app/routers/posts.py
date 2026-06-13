from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import PostCreate, PostOut
from app.repositories import posts as repo
from app.services import posts as service

router = APIRouter()

@router.get("/posts")
async def list_posts(
    q: str | None = None,
    tag: str | None = None,
    cursor: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    items, next_cursor = await repo.list_posts(session, q=q, tag=tag, cursor=cursor)
    
    return {
        "items": [PostOut.model_validate(p).model_dump(by_alias=True) for p in items],
        "nextCursor": next_cursor,                                                   
    }
    

@router.get("/posts/{post_id}", response_model=PostOut, response_model_by_alias=True)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_db)
):
    post = await repo.get_post(session, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.post("/posts", response_model=PostOut, response_model_by_alias=True, status_code=201)
async def create_post(
    body: PostCreate,
    session: AsyncSession = Depends(get_db),
):
    try:
        post = await service.create(session, body, author_id=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
    return post