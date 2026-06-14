from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import PostCreate, PostOut, PostType
from app.repositories import posts as repo
from app.services import posts as service
from app.auth.deps import get_current_user, get_current_user_optional
from app.models import User

router = APIRouter()

@router.get("/posts")
async def list_posts(
    q: str | None = None,
    tag: str | None = None,
    post_type: PostType | None = Query(default=None, alias="postType"),
    cursor: str | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    items, next_cursor = await repo.list_posts(
        session,
        q=q,
        tag=tag,
        post_type=post_type,
        cursor=cursor,
        user_id=user_id,
    )
    
    return {
        "items": [PostOut.model_validate(p).model_dump(by_alias=True) for p in items],
        "nextCursor": next_cursor,                                                   
    }
    

@router.get("/posts/{post_id}", response_model=PostOut, response_model_by_alias=True)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    post = await repo.get_post(session, post_id, user_id=user_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.post("/posts", response_model=PostOut, response_model_by_alias=True, status_code=201)
async def create_post(
    body: PostCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        post = await service.create(session, body, author_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    post.author_name = current_user.username
    post.comment_count = 0
    post.my_vote = 0
    return post
