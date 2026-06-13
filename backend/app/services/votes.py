from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Vote
from app.repositories.comments import get_comment
from app.repositories.posts import get_post
from app.repositories.votes import count_votes, get_vote


async def vote_post(
    session: AsyncSession,
    post_id: int,
    user_id: int,
    value: int,
) -> tuple[int, int]:                      
    post = await get_post(session, post_id)
    if post is None:
        raise LookupError("post not found")

    existing = await get_vote(session, user_id, post_id)

    if existing is None:                   
        session.add(Vote(
            user_id=user_id, target_type="post",
            target_id=post_id, value=value,
        ))
        post.score += value
        my_vote = value
    elif existing.value == value:
        await session.delete(existing)
        post.score -= value
        my_vote = 0
    else:                                  
        post.score += (value - existing.value)        
        existing.value = value
        my_vote = value

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ValueError("vote conflict, please retry")
    return post.score, my_vote


async def toggle_comment_like(
    session: AsyncSession,
    comment_id: int,
    user_id: int,
) -> tuple[int, bool]:
    comment = await get_comment(session, comment_id)
    if comment is None:
        raise LookupError("comment not found")

    existing = await get_vote(
        session, user_id, comment_id, target_type="comment",
    )
    if existing is None:
        session.add(Vote(
            user_id=user_id,
            target_type="comment",
            target_id=comment_id,
            value=1,
        ))
        my_like = True
    else:
        await session.delete(existing)
        my_like = False

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ValueError("like conflict, please retry")
    like_count = await count_votes(
        session, target_type="comment", target_id=comment_id, value=1,
    )
    return like_count, my_like
