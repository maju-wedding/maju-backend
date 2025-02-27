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
    category_id: int | None = Field(default=None, foreign_key="categories.id")
    order: int = Field(default=0)  # 추천 항목 정렬용


class UserChecklist(SQLModel, table=True):
    """사용자 체크리스트"""

    __tablename__ = "user_checklists"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    suggest_item_id: int | None = Field(
        default=None, foreign_key="suggest_checklist.id"
    )
    user_id: UUID = Field(foreign_key="users.id")
    is_completed: bool = Field(default=False)
    completed_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    category_id: int | None = Field(default=None, foreign_key="categories.id")
    is_deleted: bool = Field(default=False)
    order: int = Field(default=0)  # 사용자 정의 정렬용


class UserChecklistCreate(SQLModel):
    """사용자 정의 체크리스트 항목 생성 스키마"""

    title: str
    description: str | None = None
    category_id: int | None = None


class UserChecklistUpdate(SQLModel):
    """체크리스트 항목 업데이트 스키마"""

    title: str | None = None
    description: str | None = None
    category_id: int | None = None
    is_completed: bool | None = None


class ChecklistOrderUpdate(SQLModel):
    """체크리스트 항목 순서 업데이트 스키마"""

    id: int
    order: int


class UserChecklistResponse(SQLModel):
    """체크리스트 항목 응답 스키마"""

    id: int
    title: str
    description: str | None = None
    suggest_item_id: int | None = None
    user_id: UUID
    is_completed: bool
    completed_datetime: datetime | None = None
    category_id: int | None = None
    order: int = 0
