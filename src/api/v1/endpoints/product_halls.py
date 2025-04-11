from fastapi import APIRouter, Query, Depends, Path, HTTPException
from sqlalchemy.orm import selectinload
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
    query = select(Product).where(Product.is_deleted == False)

    query = query.options(
        selectinload(Product.images),
        selectinload(Product.product_hall).selectinload(
            ProductHall.product_hall_venues
        ),
    )

    if sidos:
        query = query.where(Product.sido.in_(sidos))

    if guguns:
        query = query.where(Product.gugun.in_(guguns))

    if guest_counts or wedding_types or food_menus or hall_types or hall_styles:
        query = query.join(ProductHall, Product.id == ProductHall.product_id)
        query = query.join(
            ProductHallVenue, ProductHall.id == ProductHallVenue.product_hall_id
        )

        if guest_counts:
            guest_count_filters = []
            for count_range in guest_counts:
                min_count, max_count = parse_guest_count_range(count_range)

                if min_count is not None and max_count is not None:
                    guest_count_filters.append(
                        and_(
                            ProductHallVenue.guaranteed_min_count >= min_count,
                            ProductHallVenue.guaranteed_min_count <= max_count,
                        )
                    )
                elif min_count is not None:
                    guest_count_filters.append(
                        ProductHallVenue.guaranteed_min_count >= min_count
                    )
                elif max_count is not None:
                    guest_count_filters.append(
                        ProductHallVenue.guaranteed_min_count <= max_count
                    )

            if guest_count_filters:
                query = query.where(or_(*guest_count_filters))

        if wedding_types:
            query = query.where(ProductHallVenue.wedding_type.in_(wedding_types))

        if food_menus:
            query = query.where(ProductHallVenue.food_menu.in_(food_menus))

        if hall_types:
            query = query.where(ProductHallVenue.hall_types.in_(hall_types))

        if hall_styles:
            query = query.where(ProductHallVenue.hall_styles.in_(hall_styles))

        query = query.distinct(Product.id)

    query = query.offset(offset).limit(limit)

    result = await session.stream(query)
    products = await result.unique().scalars().all()

    response_data = []
    for product in products:
        image_urls = [img.image_url for img in product.images if not img.is_deleted]

        response_data.append(
            {
                "id": product.id,
                "hashtags": product.hashtag.split(",") if product.hashtag else [],
                "name": product.name,
                "sido": product.sido,
                "gugun": product.gugun,
                "address": product.address,
                "image_urls": image_urls,
            }
        )

    return response_data


@router.get("/search", response_model=list[ProductHallSearchRead])
async def search_wedding_halls(
    q: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = select(Product).where(Product.is_deleted == False)

    query = query.options(selectinload(Product.product_hall))

    query = query.filter(
        or_(
            Product.name.ilike(f"%{q}%"),
            ProductHallVenue.name.ilike(f"%{q}%"),
        )
    )

    query = query.offset(offset).limit(limit)

    result = await session.stream(query)
    products = await result.scalars().all()

    return [
        {
            "id": product.id,
            "name": product.name,
            "sido": product.sido,
            "gugun": product.gugun,
            "address": product.address,
            "thumbnail_url": product.thumbnail_url,
            "subway_line": product.subway_line,
            "subway_name": product.subway_name,
        }
        for product in products
    ]


@router.get("/{product_id}", response_model=ProductHallRead)
async def get_wedding_hall(
    product_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    query = select(Product).where(
        and_(
            Product.id == product_id,
            Product.is_deleted == False,
        )
    )

    query = query.options(
        *[
            selectinload(Product.images),
            selectinload(Product.ai_reviews),
            selectinload(Product.scores),
            selectinload(Product.product_hall).selectinload(
                ProductHall.product_hall_venues,
            ),
        ]
    )

    result = await session.stream(query)
    product = await result.scalar_one_or_none()

    if not product or not product.product_hall:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "name": product.name,
        "subway_line": product.subway_line,
        "subway_name": product.subway_name,
        "way_text": product.way_text,
        "park_limit": product.park_limit,
        "park_free_hours": product.park_free_hours,
        "sido": product.sido,
        "gugun": product.gugun,
        "dong": product.dong,
        "address": product.address,
        "hall": product.product_hall,
        "venues": product.product_hall.product_hall_venues,
        "ai_reviews": product.ai_reviews,
        "scores": product.scores,
    }
