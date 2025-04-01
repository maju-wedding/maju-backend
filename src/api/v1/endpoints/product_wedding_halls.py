from fastapi import APIRouter, Query, Depends
from sqlmodel import select, and_, distinct
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db import get_session
from models import (
    ProductHall,
    Product,
)
from models.product_hall_venues import (
    ProductHallVenue,
)

router = APIRouter()


@router.get("")
async def list_wedding_halls(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sido: str = Query(None),
    gugun: str = Query(None),
    wedding_types: list[str] = Query(None),
    food_type_ids: list[int] = Query(None),
    hall_type_ids: list[int] = Query(None),
    hall_style_ids: list[int] = Query(None),
    min_capacity: int = Query(None),
    max_capacity: int = Query(None),
    session: AsyncSession = Depends(get_session),
):
    # 필터 조건 설정
    filters = [Product.is_deleted == False, Product.product_category_id == 1]

    # 제품 관련 필터 적용
    if sido:
        filters.append(Product.sido.like(f"%{sido}%"))

    if gugun:
        filters.append(Product.gugun.like(f"%{gugun}%"))

    # 베뉴 관련 필터 설정
    venue_filters = []

    if food_type_ids:
        venue_filters.append(ProductHallVenue.food_type_id.in_(food_type_ids))

    if wedding_types:
        venue_filters.append(ProductHallVenue.wedding_type.in_(wedding_types))

    if min_capacity:
        venue_filters.append(ProductHallVenue.min_capacity >= min_capacity)

    if max_capacity:
        venue_filters.append(ProductHallVenue.max_capacity <= max_capacity)

    # 1단계: 모든 필터 조건을 적용하여 제품 ID 조회
    product_ids_query = (
        select(distinct(Product.id))
        .join(ProductHall, ProductHall.product_id == Product.id)
        .join(ProductHallVenue, ProductHallVenue.product_hall_id == ProductHall.id)
        .where(and_(*filters))
    )

    # 베뉴 필터 적용
    if venue_filters:
        product_ids_query = product_ids_query.where(and_(*venue_filters))

    # hall_types 필터 적용

    # 제품 ID 목록 가져오기
    result = await session.execute(product_ids_query)
    product_ids = [row[0] for row in result.all()]

    # 2단계: 필터링된 ID를 사용하여 제품 상세 정보 조회
    if product_ids:
        products_query = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(products_query)
        products = result.scalars().all()

        # 결과를 직렬화 가능한 형태로 변환
        response_data = []
        for product in products:
            response_data.append(product)

        return response_data
    else:
        return []
