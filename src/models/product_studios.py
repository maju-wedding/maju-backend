from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_studio_packages import ProductStudioPackage
    from models.products import Product


class ProductStudio(SQLModel, table=True):
    __tablename__ = "product_studios"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)

    # 스튜디오 특성 (모든 패키지에 공통적인 특성)
    has_garden_scene: bool = Field(default=False)
    has_road_scene: bool = Field(default=False)
    has_rooftop_scene: bool = Field(default=False)
    has_night_scene: bool = Field(default=False)
    has_hanbok_scene: bool = Field(default=False)
    has_pet_scene: bool = Field(default=False)
    has_black_white_scene: bool = Field(default=False)

    # 서비스 관련
    hair_makeup_available: bool = Field(default=False)

    # 시스템 필드
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

    # 관계
    product: "Product" = Relationship(back_populates="product_studio")
    studio_packages: list["ProductStudioPackage"] = Relationship(
        back_populates="product_studio"
    )
