from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from models.product_hall_venues import ProductHallVenue
from models.products import Product
from utils.utils import utc_now


class ProductHall(SQLModel, table=True):
    __tablename__ = "product_halls"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)
    name: str = Field(max_length=100)

    # amenities
    elevator_count: int = Field(default=0)
    atm_count: int = Field(default=0)
    contain_family_waiting_room: bool = Field(default=False)
    contain_pyebaek_room: bool = Field(default=False)

    valet_parking: bool = Field(default=False)
    dress_room: bool = Field(default=False)
    smoking_area: bool = Field(default=False)
    photo_zone: bool = Field(default=False)

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

    # Relationships
    product: "Product" = Relationship(back_populates="product_hall")
    product_hall_venues: list["ProductHallVenue"] = Relationship(
        back_populates="product_hall"
    )
