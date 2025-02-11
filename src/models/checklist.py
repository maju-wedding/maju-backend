from datetime import datetime

from sqlmodel import SQLModel, Field


class SuggestChecklist(SQLModel, table=True):
    """시스템 제공 기본 체크리스트"""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    recommended_timeline: int | None = Field(
        default=None, description="결혼일 기준 몇일 전까지"
    )
    category_id: int | None = Field(default=None, foreign_key="category.id")


class UserChecklist(SQLModel, table=True):
    """사용자 체크리스트"""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    default_item_id: int = Field(foreign_key="suggestchecklist.id")
    user_id: int
    deadline: datetime | None = None
    is_completed: bool = Field(default=False)
    completed_at: datetime | None = None
    category_id: int | None = Field(default=None, foreign_key="category.id")
