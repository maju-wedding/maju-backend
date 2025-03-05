from datetime import datetime
from typing import TYPE_CHECKING

import sqlmodel
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel, Relationship

from core.enums import CategoryTypeEnum
from utils.utils import utc_now

if TYPE_CHECKING:
    from models import Product


class ProductCategory(SQLModel, table=True):
    __tablename__ = "product_categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=20)
    display_name: str = Field(max_length=10)
    type: CategoryTypeEnum = Field(sa_column=Column(String))
    is_ready: bool = Field(default=False)
    order: int = Field(default=0, ge=0)
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

    products: list["Product"] = Relationship(back_populates="category")
