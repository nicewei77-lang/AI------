from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

from app.ai.schemas import ProjectAnalysisReport, ReportStatus

PostType = Literal["project", "idea"]
AnalysisStatus = Literal["not_started", "running", "completed", "failed", "need_more_info"]


class PostCreate(BaseModel):
    """글 작성 요청 body. 사용자가 직접 적는 필드만 포함(id·createdAt·AI 분석 결과 제외)."""
    title: str
    body: str
    tag_ids: list[str] = Field(default_factory=list, alias="tagIds")
    post_type: PostType = Field(default="project", alias="postType")
    service_url: str | None = Field(default=None, alias="serviceUrl")
    github_url: str | None = Field(default=None, alias="githubUrl")
    one_liner: str | None = Field(default=None, alias="oneLiner")
    target_user: str | None = Field(default=None, alias="targetUser")
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")
    
    model_config = ConfigDict(populate_by_name=True)
    

class TagOut(BaseModel):
    """ORM TAG(.slug/.name/.id) → 프론트 Tag({id, label})."""
    id: str = Field(validation_alias="slug")
    label: str = Field(validation_alias="name")
    model_config = ConfigDict(from_attributes=True)


class PostOut(BaseModel):
    """글 작성 요청 1개 응답."""
    id: int
    author_name: str = Field(alias="authorName")
    title: str
    body: str
    post_type: PostType = Field(alias="postType")
    service_url: str | None = Field(default=None, alias="serviceUrl")
    github_url: str | None = Field(default=None, alias="githubUrl")
    one_liner: str | None = Field(default=None, alias="oneLiner")
    target_user: str | None = Field(default=None, alias="targetUser")
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")
    analysis_status: AnalysisStatus = Field(alias="analysisStatus")
    ai_summary: str | None = Field(default=None, alias="aiSummary")
    created_at: datetime = Field(alias="createdAt")
    score: int
    my_vote: int = Field(default=0, alias="myVote")   # 현재 사용자의 투표(1/-1), 없거나 비로그인=0
    comment_count: int = Field(default=0, alias="commentCount")
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
    author_name: str = Field(alias="authorName")
    created_at: datetime = Field(alias="createdAt")
    like_count: int = Field(default=0, alias="likeCount")
    my_like: bool = Field(default=False, alias="myLike")
    
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


class CommentLikeOut(BaseModel):
    """댓글 좋아요 응답: {likeCount, myLike}"""
    like_count: int = Field(alias="likeCount")
    my_like: bool = Field(alias="myLike")
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


class AnalysisRunOut(BaseModel):
    """동기 AI 분석 실행 응답."""

    status: ReportStatus
    report_id: int = Field(alias="reportId")
    report: ProjectAnalysisReport
    error: dict | None = None

    model_config = ConfigDict(populate_by_name=True)


class AnalysisLatestOut(AnalysisRunOut):
    """최신 AI 분석 리포트 응답."""

    created_at: datetime | None = Field(default=None, alias="createdAt")
    model: str | None = None
    reasoning_effort: str | None = Field(default=None, alias="reasoningEffort")
    response_id: str | None = Field(default=None, alias="responseId")
    trace_id: str | None = Field(default=None, alias="traceId")
    usage: dict | None = None

    model_config = ConfigDict(populate_by_name=True)
