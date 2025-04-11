from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlmodel
from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.checklist_categories import ChecklistCategory


class Checklist(SQLModel, table=True):
    __tablename__ = "checklists"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = Field(default=None, sa_column=Column(Text))
    checklist_category_id: int | None = Field(
        default=None, foreign_key="checklist_categories.id"
    )
    is_system_checklist: bool = Field(default=False)
    user_id: UUID | None = Field(foreign_key="users.id")
    global_display_order: int = Field(
        default=0, sa_column=Column(sqlmodel.Integer, default=0)
    )
    category_display_order: int = Field(
        default=0, sa_column=Column(sqlmodel.Integer, default=0)
    )

    is_completed: bool = Field(default=False)
    completed_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
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

    is_deleted: bool = Field(default=False)

    checklist_category: "ChecklistCategory" = Relationship(back_populates="checklists")
