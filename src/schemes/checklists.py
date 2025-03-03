from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel, Field

from utils.utils import utc_now


class ChecklistCategoryCreateBySystem(SQLModel):
    """시스템 제공 체크리스트 카테고리 생성 스키마"""

    display_name: str


class ChecklistCategoryCreate(SQLModel):
    """체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool = False


class InternalChecklistCategoryCreate(SQLModel):
    """내부용 체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool
    user_id: UUID | None = None
    created_datetime: datetime | None = Field(default_factory=utc_now)


class ChecklistCategoryUpdate(SQLModel):
    """체크리스트 카테고리 업데이트 스키마"""

    display_name: str | None = None


class ChecklistCategoryRead(SQLModel):
    """체크리스트 카테고리 읽기 스키마"""

    id: int
    display_name: str
    is_system_category: bool
    user_id: UUID | None = None


class ChecklistCreate(SQLModel):
    """사용자 정의 체크리스트 항목 생성 스키마"""

    title: str
    description: str | None = None
    checklist_category_id: int


class InternalChecklistCreate(SQLModel):
    """내부용 체크리스트 항목 생성 스키마"""

    title: str
    description: str | None = None
    checklist_category_id: int
    user_id: UUID | None = None
    is_system_checklist: bool


class ChecklistUpdate(SQLModel):
    """체크리스트 항목 업데이트 스키마"""

    title: str | None = None
    description: str | None = None
    checklist_category_id: int | None = None
    is_completed: bool | None = None


class ChecklistOrderUpdate(SQLModel):
    """체크리스트 항목 순서 업데이트 스키마"""

    id: int
    display_order: int


class ChecklistRead(SQLModel):
    """체크리스트 항목 응답 스키마"""

    id: int
    title: str
    description: str | None = None
    user_id: UUID | None = None
    is_completed: bool
    completed_datetime: datetime | None = None
    checklist_category_id: int | None = None
    display_order: int = 0


class SuggestChecklistRead(SQLModel):

    id: int
    title: str
    description: str | None = None
    checklist_category_id: int | None = None
    display_order: int = 0
