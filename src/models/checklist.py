from datetime import datetime
from uuid import UUID

import sqlmodel
from sqlmodel import SQLModel, Field


class SuggestChecklist(SQLModel, table=True):
    """시스템 제공 기본 체크리스트"""

    __tablename__ = "suggest_checklist"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    recommended_timeline: int | None = Field(
        default=None, description="결혼일 기준 몇일 전까지"
    )
    category_id: int | None = Field(default=None, foreign_key="categories.id")


class UserChecklist(SQLModel, table=True):
    """사용자 체크리스트"""

    __tablename__ = "user_checklists"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    suggest_item_id: int = Field(foreign_key="suggest_checklist.id")
    user_id: UUID = Field(foreign_key="users.id")
    deadline: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    is_completed: bool = Field(default=False)
    completed_at: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    category_id: int | None = Field(default=None, foreign_key="categories.id")
