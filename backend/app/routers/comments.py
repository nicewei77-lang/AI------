from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import CommentCreate, CommentOut
from app.repositories import comments as repo
from app.services import comments as service

router = APIRouter()


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut], response_model_by_alias=True)
async def list_comments(
    post_id: int,                                     
    session: AsyncSession = Depends(get_db),
):
    return await repo.list_comments(session, post_id)


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
):
    try:
        comment = await service.create(
            session, post_id, author_id=1, body=body.body,
        )
    except LookupError as e:                                  
        raise HTTPException(status_code=404, detail=str(e))   
    return comment
