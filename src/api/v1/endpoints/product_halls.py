import sys

from fastapi import APIRouter, Query, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import product as crud_product
from crud import product_ai_review as crud_review
from crud import product_hall as crud_hall
from crud import product_score as crud_score
from schemes.product_halls import (
    ProductHallListRead,
    ProductHallSearchRead,
    ProductHallRead,
)

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
    """웨딩홀 목록 조회"""
    halls = await crud_hall.filter_halls(
        db=session,
        skip=offset,
        limit=limit,
        sidos=sidos,
        guguns=guguns,
        guest_counts=guest_counts,
        wedding_types=wedding_types,
        food_menus=food_menus,
        hall_types=hall_types,
        hall_styles=hall_styles,
    )

    response_data = []
    for hall in halls:
        product = await crud_product.get_with_details(
            db=session, product_id=hall.product_id, load_images=True
        )

        if product:
            image_urls = [img.image_url for img in product.images][:6]

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
    """웨딩홀 검색"""
    products = await crud_product.search_products(
        db=session, search_term=q, skip=offset, limit=limit
    )

    return [
        ProductHallSearchRead(
            id=product.id,
            name=product.name,
            sido=product.sido,
            gugun=product.gugun,
            address=product.address,
            thumbnail_url=product.thumbnail_url or "",
            subway_line=product.subway_line,
            subway_name=product.subway_name,
        )
        for product in products
    ]


@router.get("/{product_id}", response_model=ProductHallRead)
async def get_wedding_hall(
    product_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """웨딩홀 상세 조회"""
    product = await crud_product.get_with_images_and_hall_using_joins(
        db=session, product_id=product_id
    )

    if not product or not product.product_hall:
        raise HTTPException(status_code=404, detail="Product not found")

    # AI 리뷰 가져오기
    ai_reviews = await crud_review.get_by_product(db=session, product_id=product_id)
    for ai_review in ai_reviews:
        ai_review.content = "\n".join(
            f"* {item}" for item in ai_review.content.split("|")
        )

    # 점수 정보 가져오기
    scores = await crud_score.get_by_product(db=session, product_id=product_id)

    max_price = 0
    min_price = sys.maxsize
    for venue in product.product_hall.product_hall_venues:
        max_price = max(
            venue.peak_season_price
            + venue.guaranteed_min_count * venue.food_cost_per_adult,
            max_price,
        )
        min_price = min(
            venue.basic_price + venue.guaranteed_min_count * venue.food_cost_per_adult,
            min_price,
        )

    return ProductHallRead(
        id=product.id,
        name=product.name,
        hashtags=product.hashtag.split(",") if product.hashtag else [],
        subway_line=product.subway_line,
        subway_name=product.subway_name,
        way_text=product.way_text,
        park_limit=product.park_limit or 0,
        park_free_hours=product.park_free_hours or 0,
        sido=product.sido,
        gugun=product.gugun,
        dong=product.dong or "",
        address=product.address,
        has_single_hall=len(product.product_hall.product_hall_venues) == 1,
        max_price=max_price,
        min_price=min_price,
        hall=product.product_hall,
        venues=product.product_hall.product_hall_venues,
        ai_reviews=ai_reviews,
        scores=scores,
    )
