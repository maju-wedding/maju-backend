from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlmodel
from sqlalchemy import Column, Text, DateTime
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.users import User
    from models.categories import Category


class UserSpent(SQLModel, table=True):
    """사용자의 카테고리별 지출 항목"""

    __tablename__ = "user_spents"

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    category_id: int = Field(foreign_key="categories.id")
    amount: int = Field(default=0)
    title: str = Field(default="")
    memo: str | None = Field(sa_column=Column(Text), default=None)

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
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    category: "Category" = Relationship(back_populates="user_spents")
    user: "User" = Relationship(back_populates="user_spents")
