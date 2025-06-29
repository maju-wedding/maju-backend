from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.user_spents import UserSpent
    from models.checklists import Checklist


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    display_name: str
    is_system_category: bool = Field(default=False)
    user_id: UUID | None = Field(default=None, nullable=True, foreign_key="users.id")
    icon_url: str | None = Field(default=None, nullable=True)
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

    checklists: list["Checklist"] = Relationship(back_populates="category")
    user_spents: list["UserSpent"] = Relationship(back_populates="category")

    def __str__(self):
        return f"[{self.id}] {self.display_name}"
