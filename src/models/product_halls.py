from datetime import datetime

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from models.products import Product
from utils.utils import utc_now


class ProductHall(SQLModel, table=True):
    __tablename__ = "product_halls"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)
    name: str = Field(max_length=100, nullable=True)
    hall_type: str = Field(
        max_length=255
    )  # 채플, 호텔, 컨벤션, 하우스, 야외, 한옥, 소규모, 기타
    hall_style: str = Field(max_length=255)  # 밝은, 어두운

    # hall size
    min_capacity: int = Field(default=0)
    max_capacity: int = Field(default=0)
    guaranteed_min_count: int = Field(default=0)

    # hall detail
    wedding_type: str = Field(max_length=10)  # 동시, 분리
    wedding_running_time: int = Field(default=60)  # 60분

    # food
    food_type: str = Field(max_length=255)  # 뷔페, 코스, 한상
    food_cost: int
    # 코스 130,000원

    # amenities
    elevator: bool
    valet_parking: bool
    pyebaek_room: bool
    family_waiting_room: bool

    atm: bool
    dress_room: bool
    smoking_area: bool
    photo_zone: bool

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
