import sys

from fastapi import APIRouter, Query, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import product as crud_product
from crud import product_ai_review as crud_review
from crud import product_hall as crud_hall
from crud import product_image as crud_image
from crud import product_score as crud_score
from schemes.product_halls import (
    ProductHallListRead,
    ProductHallSearchRead,
    ProductHallRead,
    HallVenueRead,
    HallVenueAmenitiesRead,
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


@router.get("/count", response_model=dict)
async def get_wedding_halls_count(
    sidos: list[str] = Query(None),
    guguns: list[str] = Query(None),
    guest_counts: list[str] = Query(None),
    wedding_types: list[str] = Query(None),
    food_menus: list[str] = Query(None),
    hall_types: list[str] = Query(None),
    hall_styles: list[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """웨딩홀 개수 조회 (필터 적용)"""

    # 동일한 필터링 로직을 사용하여 개수 조회
    count = await crud_hall.count_filtered_halls(
        db=session,
        sidos=sidos,
        guguns=guguns,
        guest_counts=guest_counts,
        wedding_types=wedding_types,
        food_menus=food_menus,
        hall_types=hall_types,
        hall_styles=hall_styles,
    )

    return {"count": count}


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

    # 점수 비교 정보 가져오기
    score_summary = await crud_score.get_hall_score_comparison(
        db=session, product_id=product_id
    )

    # venue 이미지 정보 가져오기
    venue_ids = [venue.id for venue in product.product_hall.product_hall_venues]
    venue_images_map = await crud_image.get_venue_amenities_images_for_venues(
        db=session, product_id=product_id, venue_ids=venue_ids
    )

    max_price = 0
    min_price = sys.maxsize
    venues_data = []

    for venue in product.product_hall.product_hall_venues:
        # 가격 계산
        max_price = max(
            venue.peak_season_price
            + venue.guaranteed_min_count * venue.food_cost_per_adult,
            max_price,
        )
        min_price = min(
            venue.basic_price + venue.guaranteed_min_count * venue.food_cost_per_adult,
            min_price,
        )

        # venue 이미지 정보 가져오기
        venue_images = venue_images_map.get(venue.id, [])

        # 이미지 타입별로 URL 분류
        bride_room_images = [
            img.image_url for img in venue_images if img.image_type == "신부대기실"
        ]
        pyebaek_room_images = [
            img.image_url for img in venue_images if img.image_type == "폐백실"
        ]
        banquet_hall_images = [
            img.image_url for img in venue_images if img.image_type == "연회장"
        ]

        # amenities 정보 구성
        amenities_info = HallVenueAmenitiesRead(
            has_bride_room=venue.has_bride_room,
            has_pyebaek_room=venue.has_pyebaek_room,
            has_banquet_hall=venue.has_banquet_hall,
            bride_room_image_urls=bride_room_images,
            pyebaek_room_image_urls=pyebaek_room_images,
            banquet_hall_image_urls=banquet_hall_images,
        )

        # venue 데이터 구성
        venue_data = HallVenueRead(
            id=venue.id,
            name=venue.name,
            wedding_interval=venue.wedding_interval,
            wedding_times=venue.wedding_times,
            wedding_type=venue.wedding_type,
            hall_styles=venue.hall_styles,
            hall_types=venue.hall_types,
            guaranteed_min_count=venue.guaranteed_min_count,
            min_capacity=venue.min_capacity,
            max_capacity=venue.max_capacity,
            basic_price=venue.basic_price,
            peak_season_price=venue.peak_season_price,
            ceiling_height=venue.ceiling_height,
            virgin_road_length=venue.virgin_road_length,
            include_drink=venue.include_drink,
            include_alcohol=venue.include_alcohol,
            include_service_fee=venue.include_service_fee,
            include_vat=venue.include_vat,
            bride_room_entry_methods=venue.bride_room_entry_methods,
            bride_room_makeup_room=venue.bride_room_makeup_room,
            food_menu=venue.food_menu,
            food_cost_per_adult=venue.food_cost_per_adult,
            food_cost_per_child=venue.food_cost_per_child,
            banquet_hall_running_time=venue.banquet_hall_running_time,
            banquet_hall_max_capacity=venue.banquet_hall_max_capacity,
            additional_info=venue.additional_info,
            special_notes=venue.special_notes,
            amenities_info=amenities_info,
            images=venue.images,
        )
        venues_data.append(venue_data)

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
        hall_amenities_info=product.product_hall,
        venues=venues_data,
        ai_reviews=ai_reviews,
        ai_score_summary=score_summary,
    )
