from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel

from schemes.checklists import ChecklistCategoryRead


class UserSpentCreate(SQLModel):
    """지출 항목 생성 스키마"""

    category_id: int
    amount: int
    title: str
    memo: str | None = None


class UserSpentUpdate(SQLModel):
    """지출 항목 수정 스키마"""

    amount: int | None = None
    title: str | None = None
    memo: str | None = None
    category_id: int | None = None


class UserSpentRead(SQLModel):
    """지출 항목 응답 스키마"""

    id: int
    user_id: UUID
    category_id: int
    amount: int
    title: str
    memo: str | None = None
    created_datetime: datetime
    updated_datetime: datetime
    is_deleted: bool


class UserSpentWithCategory(UserSpentRead):
    """카테고리 정보가 포함된 지출 항목 응답"""

    category: ChecklistCategoryRead | None = None


class BudgetSummary(SQLModel):
    """예산 요약 정보"""

    total_budget: int  # 총 예산
    total_spent: int  # 총 지출
    remaining_budget: int  # 남은 예산
    budget_usage_percentage: float  # 예산 사용률 (%)


class CategorySpentSummary(SQLModel):
    """카테고리별 지출 요약"""

    category: ChecklistCategoryRead
    total_spent: int
    spent_count: int  # 지출 건수


class BudgetDashboard(SQLModel):
    """예산 대시보드 전체 정보"""

    budget_summary: BudgetSummary
    category_summaries: list[CategorySpentSummary]
