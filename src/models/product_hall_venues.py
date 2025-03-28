from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_halls import ProductHall


class ProductHallVenueTypeLink(SQLModel, table=True):
    __tablename__ = "product_hall_venue_type_links"

    venue_id: int = Field(foreign_key="product_hall_venues.id", primary_key=True)
    hall_type_id: int = Field(foreign_key="product_hall_types.id", primary_key=True)

    # Relationships
    venue: "ProductHallVenue" = Relationship(back_populates="venue_type_links")
    hall_type: "ProductHallType" = Relationship(back_populates="venue_type_links")


class ProductHallStyleLink(SQLModel, table=True):
    __tablename__ = "product_hall_style_links"

    venue_id: int = Field(foreign_key="product_hall_venues.id", primary_key=True)
    hall_style_id: int = Field(foreign_key="product_hall_styles.id", primary_key=True)

    # Relationships
    venue: "ProductHallVenue" = Relationship(back_populates="hall_style_links")
    hall_style: "ProductHallStyle" = Relationship(back_populates="hall_style_links")


class ProductHallStyle(SQLModel, table=True):
    __tablename__ = "product_hall_styles"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(...)

    hall_style_links: list["ProductHallStyleLink"] = Relationship(
        back_populates="hall_style"
    )
    venues: list["ProductHallVenue"] = Relationship(
        back_populates="hall_styles",
        link_model=ProductHallStyleLink,
        sa_relationship_kwargs={"overlaps": "hall_style,hall_style_links,venue"},
    )


class ProductHallType(SQLModel, table=True):
    __tablename__ = "product_hall_types"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(...)

    venue_type_links: list["ProductHallVenueTypeLink"] = Relationship(
        back_populates="hall_type"
    )
    venues: list["ProductHallVenue"] = Relationship(
        back_populates="hall_types",
        link_model=ProductHallVenueTypeLink,
        sa_relationship_kwargs={"overlaps": "venue_type_links,venue,hall_type"},
    )


class ProductHallFoodType(SQLModel, table=True):
    __tablename__ = "product_hall_food_types"
    # 뷔페, 코스, 한상

    id: int = Field(default=None, primary_key=True)
    name: str = Field(...)

    venues: list["ProductHallVenue"] = Relationship(back_populates="food_type")


class ProductHallVenue(SQLModel, table=True):
    __tablename__ = "product_hall_venues"

    id: int = Field(default=None, primary_key=True)
    product_hall_id: int = Field(foreign_key="product_halls.id")
    name: str = Field(...)

    # hall detail
    wedding_interval: int = Field(default=60)  # 60분
    wedding_times: str = Field(...)
    wedding_type: str = Field(max_length=10)  # 동시, 분리

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
    food_type_id: int = Field(foreign_key="product_hall_food_types.id")
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
    hall_style_links: list["ProductHallStyleLink"] = Relationship(
        back_populates="venue", sa_relationship_kwargs={"overlaps": "venues"}
    )
    hall_styles: list["ProductHallStyle"] = Relationship(
        back_populates="venues",
        link_model=ProductHallStyleLink,
        sa_relationship_kwargs={
            "overlaps": "hall_style_links,venue,hall_style,hall_style_links"
        },
    )

    venue_type_links: list["ProductHallVenueTypeLink"] = Relationship(
        back_populates="venue", sa_relationship_kwargs={"overlaps": "venues"}
    )
    hall_types: list["ProductHallType"] = Relationship(
        back_populates="venues",
        link_model=ProductHallVenueTypeLink,
        sa_relationship_kwargs={
            "overlaps": "venue,venue_type_links,hall_type,venue_type_links"
        },
    )

    food_type: "ProductHallFoodType" = Relationship(back_populates="venues")
