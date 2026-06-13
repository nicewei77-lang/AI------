from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import VoteIn, VoteOut
from app.services import votes as service
from app.auth.deps import get_current_user
from app.models import User

router = APIRouter()


@router.post("/posts/{post_id}/vote", response_model=VoteOut, response_model_by_alias=True)
async def vote(
    post_id: int,
    body: VoteIn,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        score, my_vote = await service.vote_post(
            session, post_id, user_id=current_user.id, value=body.value,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return VoteOut(score=score, my_vote=my_vote)
