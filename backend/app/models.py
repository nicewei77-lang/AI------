from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    BigInteger,
    Text,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())        


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)   # UNIQUE NOT NULL
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
   
   
class Post(Base):
    __tablename__="posts"
    __table_args__ = (
        CheckConstraint("post_type IN ('project', 'idea')", name="posts_post_type_check"),
        CheckConstraint(
            "analysis_status IN ('not_started', 'running', 'completed', 'failed', 'need_more_info')",
            name="posts_analysis_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[str] = mapped_column(Text, default="project", nullable=False)
    service_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    one_liner: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_user: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    analysis_status: Mapped[str] = mapped_column(Text, default="not_started", nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    author: Mapped["User"]=relationship()
    tags: Mapped[list["Tag"]] = relationship(secondary="post_tags")
    
    
class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    post: Mapped[Post]=relationship()
    author: Mapped[User]=relationship()


class Vote(Base):
    __tablename__ = "votes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id"),)
    

class PostTag(Base):
    __tablename__ = "post_tags"
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class AiReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('completed', 'need_more_info', 'failed', 'refused')",
            name="ai_reports_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    report_type: Mapped[str | None] = mapped_column(Text, default="full_analysis")
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning_effort: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    input_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    post: Mapped[Post | None] = relationship()


class McpEvidence(Base):
    __tablename__ = "mcp_evidences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    report_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("ai_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    tool_name: Mapped[str] = mapped_column(Text, nullable=False)
    arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    post: Mapped[Post | None] = relationship()
    report: Mapped[AiReport | None] = relationship()


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('post', 'ai_report', 'comment', 'template')",
            name="embeddings_source_type_check",
        ),
        CheckConstraint("dimensions = 1536", name="embeddings_dimensions_check"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str] = mapped_column(Text, default="text-embedding-3-small", nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, default=1536, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
