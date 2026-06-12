from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class PostCreate(BaseModel):
    """글 작성 요청 body. 사용자가 직접 적는 필드만 포함(id·createdAt·verdict 제외)."""
    title: str
    excuse_text: Annotated[str, "작성 요청하는 번명글 본문 속성"] = Field(alias="excuseText")
    tag_ids: list[str] = Field(default_factory=list, alias="tagIds")
    context: dict | None = None
    
    model_config = ConfigDict(populate_by_name=True)
    
        