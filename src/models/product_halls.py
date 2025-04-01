from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_hall_venues import ProductHallVenue
    from models.products import Product


class ProductHall(SQLModel, table=True):
    __tablename__ = "product_halls"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)
    name: str | None = Field(max_length=100, nullable=True)

    # amenities
    elevator_count: int = Field(...)
    atm_count: int = Field(...)
    contain_family_waiting_room: bool = Field(...)
    contain_pyebaek_room: bool = Field(...)

    valet_parking: bool = Field(...)
    dress_room: bool = Field(...)
    smoking_area: bool = Field(...)
    photo_zone: bool = Field(...)

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
    product: "Product" = Relationship(
        back_populates="wedding_hall_detail", sa_relationship_kwargs={"uselist": False}
    )
    product_hall_venues: list["ProductHallVenue"] = Relationship(
        back_populates="product_hall"
    )
