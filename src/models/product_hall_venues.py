from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from utils.utils import utc_now

if TYPE_CHECKING:
    from models import ProductImage
    from models.product_halls import ProductHall


class ProductHallVenue(SQLModel, table=True):
    __tablename__ = "product_hall_venues"

    id: int = Field(default=None, primary_key=True)
    product_hall_id: int = Field(foreign_key="product_halls.id")
    name: str = Field(...)

    # hall detail
    wedding_interval: int = Field(default=60)  # 60분
    wedding_times: str = Field(...)
    wedding_type: str = Field(max_length=10)  # 동시, 분리
    hall_styles: str = Field(...)  # 밝음, 어두움
    hall_types: str = Field(...)  # 호텔, 채플, 컨벤션

    # hall size
    guaranteed_min_count: int = Field(default=0)
    min_capacity: int = Field(default=0)
    max_capacity: int = Field(default=0)

    basic_price: int = Field(...)
    peak_season_price: int = Field(...)

    ceiling_height: int = Field(...)
    virgin_road_length: int = Field(...)

    # drink
    include_drink: bool = Field(...)
    include_alcohol: bool = Field(...)
    include_service_fee: bool = Field(...)
    include_vat: bool = Field(...)

    # brideWaitingRoom
    bride_room_entry_methods: str = Field(...)
    bride_room_makeup_room: bool = Field(...)

    # banquetHall
    food_menu: str = Field(...)
    food_cost_per_adult: int = Field(...)
    food_cost_per_child: int = Field(...)
    banquet_hall_running_time: int = Field(...)
    banquet_hall_max_capacity: int = Field(...)

    additional_info: str = Field(max_length=255)
    special_notes: str = Field(max_length=255)

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
    product_hall: "ProductHall" = Relationship(back_populates="product_hall_venues")
    images: list["ProductImage"] = Relationship(back_populates="venue")
