from datetime import datetime
from uuid import UUID

import sqlmodel
from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field

from utils.utils import utc_now


class Checklist(SQLModel, table=True):
    """사용자 체크리스트"""

    __tablename__ = "checklists"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = Field(default=None, sa_column=Column(Text))
    checklist_category_id: int | None = Field(
        default=None, foreign_key="checklist_categories.id"
    )
    is_system_checklist: bool = Field(default=False)
    user_id: UUID | None = Field(foreign_key="users.id")
    is_completed: bool = Field(default=False)
    completed_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    is_deleted: bool = Field(default=False)
    display_order: int = Field(default=0)
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
