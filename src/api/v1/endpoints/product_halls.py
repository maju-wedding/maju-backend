from fastapi import APIRouter, Query, Depends, Path, HTTPException
from fastcrud import JoinConfig
from sqlalchemy import and_, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db import get_session
from cruds.products import products_crud
from models import (
    ProductHall,
    Product,
    ProductImage,
    ProductAIReview,
    ProductScore,
)
from models.product_hall_venues import (
    ProductHallVenue,
)
from schemes.product_halls import (
    ProductHallListRead,
    ProductHallSearchRead,
    ProductHallRead,
)
from utils.utils import parse_guest_count_range

router = APIRouter()


@router.get("", response_model=list[ProductHallListRead])
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
    base_query = (
        select(
            Product.id,
            Product.hashtag,
            Product.name,
            Product.sido,
            Product.gugun,
            Product.address,
        )
        .join(ProductHall, ProductHall.product_id == Product.id)
        .outerjoin(ProductHallVenue, ProductHallVenue.product_hall_id == ProductHall.id)
        .where(Product.is_deleted == False)
        .distinct()
    )

    # 지역(시도) 필터
    if sidos:
        base_query = base_query.where(Product.sido.in_(sidos))

    # 구군 필터
    if guguns:
        base_query = base_query.where(Product.gugun.in_(guguns))

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
            elif min_count is not None and max_count is None:
                # 최대값만 있는 경우
                guest_count_filters.append(
                    ProductHallVenue.guaranteed_min_count <= max_count
                )

        if guest_count_filters:
            base_query = base_query.where(or_(*guest_count_filters))

    # 웨딩 타입 필터
    if wedding_types:
        base_query = base_query.where(ProductHallVenue.wedding_type.in_(wedding_types))

    # 식사 메뉴 필터
    if food_menus:
        base_query = base_query.where(ProductHallVenue.food_menu.in_(food_menus))

    # 홀 타입 필터
    if hall_types:
        base_query = base_query.where(ProductHallVenue.hall_types.in_(hall_types))

    # 홀 스타일 필터
    if hall_styles:
        base_query = base_query.where(ProductHallVenue.hall_styles.in_(hall_styles))

    # 페이지네이션 적용
    base_query = base_query.offset(offset).limit(limit)

    # 쿼리 실행
    result = await session.execute(base_query)
    products = result.all()

    response_data = []
    for product in products:
        image_query = (
            select(ProductImage.image_url)
            .where(
                and_(
                    ProductImage.product_id == product.id,
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(ProductImage.order)
        )

        image_result = await session.execute(image_query)
        image_urls = [row[0] for row in image_result.all()]

        response_data.append(
            ProductHallListRead(
                id=product.id,
                hashtags=product.hashtag.split(",") if product.hashtag else [],
                name=product.name,
                sido=product.sido,
                gugun=product.gugun,
                address=product.address,
                image_urls=image_urls,
            )
        )

    return response_data


@router.get("/search", response_model=list[ProductHallSearchRead])
async def search_wedding_halls(
    q: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):

    query = (
        select(
            Product.id,
            Product.name,
            Product.sido,
            Product.gugun,
            Product.address,
            Product.thumbnail_url,
            Product.subway_line,
            Product.subway_name,
        )
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
    return result.all()


@router.get("/{product_id}", response_model=ProductHallRead)
async def get_wedding_hall(
    product_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    # 기본 product와 hall 정보 가져오기
    product_with_hall = await products_crud.get_joined(
        session,
        id=product_id,
        joins_config=[
            JoinConfig(
                model=ProductHall,
                join_on=ProductHall.product_id == Product.id,
                join_prefix="hall_",
                join_type="inner",
            ),
        ],
        nest_joins=True,
    )

    if not product_with_hall:
        raise HTTPException(status_code=404, detail="Product not found")

    hall_id = product_with_hall["hall"]["id"]

    venues = await session.execute(
        select(ProductHallVenue).where(ProductHallVenue.product_hall_id == hall_id)
    )
    venues = venues.scalars().all()

    ai_reviews = await session.execute(
        select(ProductAIReview).where(ProductAIReview.product_id == product_id)
    )
    ai_reviews = ai_reviews.scalars().all()

    scores = await session.execute(
        select(ProductScore).where(ProductScore.product_id == product_id)
    )
    scores = scores.scalars().all()

    return {
        **product_with_hall,
        "venues": venues,
        "ai_reviews": ai_reviews,
        "scores": scores,
    }
