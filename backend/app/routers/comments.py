from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import CommentCreate, CommentLikeOut, CommentOut
from app.repositories import comments as repo
from app.services import comments as service
from app.services import votes as votes_service
from app.auth.deps import get_current_user, get_current_user_optional
from app.models import User

router = APIRouter()


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut], response_model_by_alias=True)
async def list_comments(
    post_id: int,                                     
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    return await repo.list_comments(session, post_id, user_id=user_id)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentOut,
    response_model_by_alias=True,
    status_code=201,                                   
)
async def create_comment(
    post_id: int,
    body: CommentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        comment = await service.create(
            session, post_id, author_id=current_user.id, body=body.body,
        )
    except LookupError as e:                                  
        raise HTTPException(status_code=404, detail=str(e))   
    comment.author_name = current_user.username
    comment.like_count = 0
    comment.my_like = False
    return comment


@router.post(
    "/comments/{comment_id}/like",
    response_model=CommentLikeOut,
    response_model_by_alias=True,
)
async def like_comment(
    comment_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        like_count, my_like = await votes_service.toggle_comment_like(
            session, comment_id, user_id=current_user.id,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return CommentLikeOut(like_count=like_count, my_like=my_like)
