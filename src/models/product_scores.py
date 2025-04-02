from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Relationship, Field

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.products import Product


class ProductScore(SQLModel, table=True):
    __tablename__ = "product_scores"

    id: int = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    score_type: str = Field(...)
    value: float = Field(default=0.0)

    is_deleted: bool = Field(default=False)
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True)),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    # Relationship
    product: "Product" = Relationship(back_populates="scores")
