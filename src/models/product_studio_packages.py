from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Text, DateTime
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_studios import ProductStudio


class ProductStudioPackage(SQLModel, table=True):
    __tablename__ = "product_studio_packages"

    id: int | None = Field(default=None, primary_key=True)
    product_studio_id: int = Field(foreign_key="product_studios.id")

    # 패키지 기본 정보
    name: str = Field(max_length=200)
    description: str | None = Field(sa_column=Column(Text), default=None)
    original_price: int | None = Field(default=None)
    price: int = Field(default=0)
    discount_price: int | None = Field(default=None)

    # 패키지 구성요소
    album_count: int = Field(default=0)
    album_page_count: int = Field(default=0)
    frame_count: int = Field(default=0)
    include_original_data: bool = Field(default=False)
    include_edited_data: bool = Field(default=False)

    # 의상 정보
    outfit_count: int = Field(default=0)
    dress_count: int = Field(default=0)
    casual_count: int = Field(default=0)

    # 촬영 정보
    shooting_duration: int = Field(default=0)  # 분 단위

    # 추가 정보
    additional_info: str | None = Field(sa_column=Column(Text), default=None)

    # 원본 데이터 참조
    original_id: str | None = Field(max_length=50, default=None)  # 원본 시스템의 ID

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
    product_studio: "ProductStudio" = Relationship(back_populates="studio_packages")
