from sqlalchemy import select                          # (1) select 함수
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Post, Tag
from app.schemas import PostCreate
from app.repositories.posts import create_post

async def create(
    session: AsyncSession,
    body: PostCreate,
    author_id: int,
) -> Post:
    tags: list[Tag] = []
    if body.tag_ids:
        # body에 있는 slug와 일치하는 tag를 꺼내는 statement를 만들고 DB에 전송한다.
        stmt = select(Tag).where(Tag.slug.in_(body.tag_ids))
        tags = list((await session.execute(stmt)).scalars().all())
    # 입력 tags와 반환 tags의 숫자가 다르면 잘못된 입력을 줬음 에러를 반환한다.
    if len(tags) != len(set(body.tag_ids)):
        found = {t.slug for t in tags}
        missing = set(body.tag_ids) - found
        raise ValueError(f"unkown tags: {missing}")
    
    # 완성된 post를 INSERT 한다.(commit 전)
    post = await create_post(
        session,
        author_id=author_id,
        title=body.title,
        body=body.body,
        post_type=body.post_type,
        service_url=body.service_url,
        github_url=body.github_url,
        one_liner=body.one_liner,
        target_user=body.target_user,
        tech_stack=body.tech_stack,
        tags=tags,
    )
    await session.commit()
    return post
