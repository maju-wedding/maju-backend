from fastapi import APIRouter, Query, Depends
from sqlmodel import and_, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db import get_session
from models import (
    ProductHall,
    Product,
)
from models.product_hall_venues import (
    ProductHallVenue,
)
from utils.utils import parse_guest_count_range

router = APIRouter()


@router.get("")
async def list_wedding_halls(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sidos: list[str] = Query(None),
    guguns: list[str] = Query(None),
    guest_counts: list[str] = Query(None),
    wedding_types: list[str] = Query(None),
    food_menus: list[str] = Query(None),
    hall_types: list[str] = Query(None),
    hall_styles: list[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    # Base query with joins

    query = (
        select(Product)
        .join(ProductHall, ProductHall.product_id == Product.id)
        .outerjoin(ProductHallVenue, ProductHallVenue.product_hall_id == ProductHall.id)
        .where(Product.is_deleted == False)
        .distinct()
    )

    # 지역(시도) 필터
    if sidos:
        query = query.where(Product.sido.in_(sidos))

    # 구군 필터
    if guguns:
        query = query.where(Product.gugun.in_(guguns))

    # 하객수 필터
    if guest_counts:
        guest_count_filters = []
        for count_range in guest_counts:
            min_count, max_count = parse_guest_count_range(count_range)

            if min_count is not None and max_count is not None:
                # 최소값과 최대값이 모두 있는 경우
                guest_count_filters.append(
                    and_(
                        ProductHallVenue.guaranteed_min_count >= min_count,
                        ProductHallVenue.guaranteed_min_count <= max_count,
                    )
                )
            elif min_count is not None and max_count is None:
                # 최소값만 있는 경우
                guest_count_filters.append(
                    ProductHallVenue.guaranteed_min_count >= min_count
                )
            elif min_count is not None and max_count is not None:
                # 최대값만 있는 경우
                guest_count_filters.append(
                    ProductHallVenue.guaranteed_min_count <= max_count
                )

        if guest_count_filters:
            query = query.where(or_(*guest_count_filters))

    # 웨딩 타입 필터
    if wedding_types:
        query = query.where(ProductHallVenue.wedding_type.in_(wedding_types))

    # 식사 메뉴 필터
    if food_menus:
        query = query.where(ProductHallVenue.food_menu.in_(food_menus))

    # 홀 타입 필터
    if hall_types:
        query = query.where(ProductHallVenue.hall_types.in_(hall_types))

    # 홀 스타일 필터
    if hall_styles:
        query = query.where(ProductHallVenue.hall_styles.in_(hall_styles))

    # 페이지네이션 적용
    query = query.offset(offset).limit(limit)

    # 쿼리 실행
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/search")
async def search_wedding_halls(
    q: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):

    query = (
        select(Product)
        .join(ProductHall, ProductHall.product_id == Product.id)
        .outerjoin(ProductHallVenue, ProductHallVenue.product_hall_id == ProductHall.id)
        .where(Product.is_deleted == False)
        .distinct()
    )

    # 검색어 필터
    query = query.filter(
        or_(
            Product.name.ilike(f"%{q}%"),
            ProductHallVenue.name.ilike(f"%{q}%"),
        )
    )

    # 페이지네이션 적용
    query = query.offset(offset).limit(limit)

    # 쿼리 실행
    result = await session.execute(query)
    return result.scalars().all()
