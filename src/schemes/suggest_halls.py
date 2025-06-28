from sqlmodel import SQLModel, Field

from schemes.product_halls import ProductHallRead


class RecommendedHallCreate(SQLModel):
    """추천 웨딩홀 추가 스키마"""

    product_hall_id: int
    recommendation_order: int = Field(default=1, ge=1)
    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)


class RecommendedHallUpdate(SQLModel):
    """추천 웨딩홀 수정 스키마"""

    recommendation_order: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = Field(default=None)


class RecommendedHallOrderUpdate(SQLModel):
    """추천 웨딩홀 순서 변경 스키마"""

    id: int
    recommendation_order: int = Field(ge=1)


class RecommendedHallRead(SQLModel):
    """추천 웨딩홀 응답 스키마"""

    id: int
    product_hall_id: int
    recommendation_order: int
    title: str | None = None
    description: str | None = None
    is_active: bool
    product_hall: ProductHallRead
