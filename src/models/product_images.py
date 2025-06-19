from datetime import datetime
from typing import TYPE_CHECKING

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.products import Product
    from models.product_hall_venues import ProductHallVenue


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    product_venue_id: int | None = Field(
        default=None, foreign_key="product_hall_venues.id"
    )
    image_url: str = Field(max_length=500)
    image_type: str = Field(max_length=50)
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

    product: "Product" = Relationship(back_populates="images")
    venue: "ProductHallVenue" = Relationship(back_populates="images")
