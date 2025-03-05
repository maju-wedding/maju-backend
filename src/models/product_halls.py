from datetime import datetime

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from models.products import Product
from utils.utils import utc_now


class ProductHall(SQLModel, table=True):
    __tablename__ = "product_halls"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)

    checkpoint: str = Field(max_length=255)
    min_capacity: int
    max_capacity: int
    parking_capacity: int

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

    # Relationship
    product: Product = Relationship(back_populates="wedding_hall_detail")
