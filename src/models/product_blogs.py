from datetime import datetime
from typing import TYPE_CHECKING

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.products import Product


class ProductBlog(SQLModel, table=True):
    __tablename__ = "product_blogs"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    title: str
    description: str
    thumbnail_url: str | None = Field(default=None)
    link_url: str

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

    product: "Product" = Relationship(back_populates="blogs")
