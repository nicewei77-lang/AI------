from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Comment
from app.repositories.comments import create_comment
from app.repositories.posts import get_post    


async def create(
    session: AsyncSession,
    post_id: int,
    author_id: int,
    body: str,
) -> Comment:
    post = await get_post(session, post_id)
    if post is None:                              
        raise LookupError("post not found")               
    comment = await create_comment(
        session, post_id=post_id, author_id=author_id, body=body,
    )
    await session.commit()                           
    return comment
