from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Vote
from app.repositories.posts import get_post
from app.repositories.votes import get_vote


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

    await session.commit()
    return post.score, my_vote
