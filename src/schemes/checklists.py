from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class CategoryCreateBySystem(SQLModel):
    """시스템 제공 체크리스트 카테고리 생성 스키마"""

    display_name: str


class CategoryCreate(SQLModel):
    """체크리스트 카테고리 생성 스키마"""

    display_name: str
    is_system_category: bool = False
    icon_url: str | None = None


class CategoryUpdate(SQLModel):
    """체크리스트 카테고리 업데이트 스키마"""

    display_name: str | None = None
    icon_url: str | None = None


class CategoryRead(SQLModel):
    """체크리스트 카테고리 읽기 스키마"""

    id: int
    display_name: str
    is_system_category: bool
    icon_url: str | None = None
    user_id: UUID | None = None
    checklists_count: int | None = None


class CategoryReadWithChecklist(SQLModel):
    """체크리스트 카테고리 읽기 스키마"""

    id: int
    display_name: str
    is_system_category: bool
    user_id: UUID | None = None
    checklists: list["SuggestChecklistRead"] | None = None


class ChecklistCreateBySystem(SQLModel):
    """체크리스트 생성"""

    system_checklist_ids: list[int]


class ChecklistCreate(SQLModel):
    """사용자 정의 체크리스트 항목 생성 스키마"""

    title: str
    memo: str | None = None
    category_id: int


class ChecklistUpdate(SQLModel):
    """체크리스트 항목 업데이트 스키마"""

    title: str | None = None
    memo: str | None = None
    category_id: int | None = None
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
    memo: str | None = None
    user_id: UUID | None = None
    is_completed: bool
    completed_datetime: datetime | None = None
    category_id: int | None = None
    global_display_order: int | None = 0
    category_display_order: int | None = 0


class SuggestChecklistRead(SQLModel):

    id: int
    title: str
    description: str | None = None
    memo: str | None = None
    category_id: int | None = None
    global_display_order: int = 0
