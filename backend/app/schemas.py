from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Literal


class PostCreate(BaseModel):
    """글 작성 요청 body. 사용자가 직접 적는 필드만 포함(id·createdAt·verdict 제외)."""
    title: str
    excuse_text: str = Field(alias="excuseText")
    tag_ids: list[str] = Field(default_factory=list, alias="tagIds")
    context: dict | None = None
    
    model_config = ConfigDict(populate_by_name=True)
    

class TagOut(BaseModel):
    """ORM TAG(.slug/.name/.id) → 프론트 Tag({id, label})."""
    id: str = Field(validation_alias="slug")
    label: str = Field(validation_alias="name")
    model_config = ConfigDict(from_attributes=True)


class PostOut(BaseModel):
    """글 작성 요청 1개 응답."""
    id: int
    title: str
    excuse_text: str = Field(alias="excuseText")
    created_at: datetime = Field(alias="createdAt")
    score: int
    my_vote: int = Field(default=0, alias="myVote")   # 현재 사용자의 투표(1/-1), 없거나 비로그인=0
    verdict: str | None = None
    credibility: int | None = None
    context: dict | None = None
    tags: list[TagOut] = Field(default_factory=list)
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    

class CommentCreate(BaseModel):
    """댓글 1개 요청"""
    body: str
    
    model_config = ConfigDict(populate_by_name=True)
    
    
class CommentOut(BaseModel):
    """댓글 1개 응답."""
    id: int
    body: str
    author_id: int = Field(alias="authorId")
    created_at: datetime = Field(alias="createdAt")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    

class VoteIn(BaseModel):
    """투표 요청 body: {value: 1 | -1}"""
    value: Literal[1, -1]                              # (힌트: 1 또는 -1만 와야 함 — 검증은 일단 int로,
                                            #  더 빡세게 막는 법은 채운 뒤 얘기하자)
    model_config = ConfigDict(populate_by_name=True)


class VoteOut(BaseModel):
    """투표 응답: {score, myVote}"""
    score: int
    my_vote: int = Field(alias="myVote")
    model_config = ConfigDict(populate_by_name=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str             

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"