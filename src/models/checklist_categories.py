from datetime import datetime
from uuid import UUID

import sqlmodel
from sqlmodel import SQLModel, Field

from utils.utils import utc_now


class ChecklistCategory(SQLModel, table=True):
    """체크리스트 카테고리"""

    __tablename__ = "checklist_categories"

    id: int | None = Field(default=None, primary_key=True)
    display_name: str
    is_system_category: bool = Field(default=False)
    user_id: UUID | None = Field(default=None, nullable=True, foreign_key="users.id")
    is_deleted: bool = Field(default=False)
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
