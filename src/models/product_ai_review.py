from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, Column, DateTime
from sqlmodel import SQLModel, Relationship, Field

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.products import Product


class ProductAIReview(SQLModel, table=True):
    __tablename__ = "product_ai_reviews"

    id: int = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    review_type: str = Field(...)
    content: str = Field(sa_column=Column(Text))

    # 누락된 필드 추가
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
    product: "Product" = Relationship(back_populates="ai_reviews")
