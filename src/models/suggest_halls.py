from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_halls import ProductHall


class RecommendedHall(SQLModel, table=True):
    __tablename__ = "recommended_halls"
    __table_args__ = (
        UniqueConstraint(
            "product_hall_id", name="uq_recommended_halls_product_hall_id"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    product_hall_id: int = Field(foreign_key="product_halls.id", unique=True)

    # 추천 순서 (1부터 시작, 낮은 숫자가 우선순위)
    recommendation_order: int = Field(default=1, index=True)

    # 추천 제목/설명 (선택사항)
    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    # 활성화 여부
    is_active: bool = Field(default=True)

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
    product_hall: "ProductHall" = Relationship()
