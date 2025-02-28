from datetime import datetime
from uuid import UUID

import sqlmodel
from sqlmodel import SQLModel, Field

from models._mixin import DateTimeMixin


class ChecklistCategory(SQLModel, DateTimeMixin, table=True):
    """체크리스트 카테고리"""

    __tablename__ = "checklist_categories"

    id: int | None = Field(default=None, primary_key=True)
    display_name: str
    is_system_category: bool = Field(default=False)
    user_id: UUID = Field(foreign_key="users.id")
    is_deleted: bool = Field(default=False)


class ChecklistCategoryCreateBySystem(SQLModel):
    """시스템 제공 체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool = True


class ChecklistCategoryCreate(SQLModel):
    """체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool = False


class InternalChecklistCategoryCreate(SQLModel):
    """내부용 체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool
    user_id: UUID


class ChecklistCategoryUpdate(SQLModel):
    """체크리스트 카테고리 업데이트 스키마"""

    display_name: str | None = None


class SuggestChecklist(SQLModel, DateTimeMixin, table=True):
    """시스템 제공 기본 체크리스트"""

    __tablename__ = "suggest_checklist"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    checklist_category_id: int = Field(
        default=None, foreign_key="checklist_categories.id"
    )
    display_order: int = Field(default=0)  # 추천 항목 정렬용
    is_deleted: bool = Field(default=False)


class SuggestChecklistCreate(SQLModel):
    """시스템 제공 기본 체크리스트 생성 스키마"""

    title: str
    description: str | None = None
    checklist_category_id: int


class SuggestChecklistUpdate(SQLModel):
    """시스템 제공 기본 체크리스트 업데이트 스키마"""

    title: str | None = None
    description: str | None = None
    checklist_category_id: int | None = None


class UserChecklist(SQLModel, DateTimeMixin, table=True):
    """사용자 체크리스트"""

    __tablename__ = "user_checklists"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    user_id: UUID = Field(foreign_key="users.id")
    is_completed: bool = Field(default=False)
    completed_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    checklist_category_id: int | None = Field(
        default=None, foreign_key="checklist_categories.id"
    )
    is_deleted: bool = Field(default=False)
    display_order: int = Field(default=0)  # 사용자 정의 정렬용


class UserChecklistCreate(SQLModel):
    """사용자 정의 체크리스트 항목 생성 스키마"""

    title: str
    description: str | None = None
    checklist_category_id: int | None = None


class UserChecklistUpdate(SQLModel):
    """체크리스트 항목 업데이트 스키마"""

    title: str | None = None
    description: str | None = None
    checklist_category_id: int | None = None
    is_completed: bool | None = None


class ChecklistOrderUpdate(SQLModel):
    """체크리스트 항목 순서 업데이트 스키마"""

    id: int
    display_order: int


class UserChecklistResponse(SQLModel):
    """체크리스트 항목 응답 스키마"""

    id: int
    title: str
    description: str | None = None
    suggest_item_id: int | None = None
    user_id: UUID
    is_completed: bool
    completed_datetime: datetime | None = None
    checklist_category_id: int | None = None
    display_order: int = 0
