from typing import Any

from sqlalchemy import and_, select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, with_loader_criteria

from models.product_hall_venues import ProductHallVenue
from models.product_halls import ProductHall
from models.products import Product
from utils.utils import parse_guest_count_range
from .base import CRUDBase


class CRUDProductHall(CRUDBase[ProductHall, dict[str, Any], dict[str, Any], int]):
    async def get_by_product(
        self, db: AsyncSession, *, product_id: int
    ) -> ProductHall | None:
        """Get product hall by product ID"""
        query = select(ProductHall).where(
            and_(
                ProductHall.product_id == product_id,
                ProductHall.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_with_venues(
        self, db: AsyncSession, *, hall_id: int
    ) -> ProductHall | None:
        """
        Get product hall with venues loaded
        Optimized using with_loader_criteria
        """
        query = (
            select(ProductHall)
            .where(
                and_(
                    ProductHall.id == hall_id,
                    ProductHall.is_deleted == False,
                )
            )
            .options(
                with_loader_criteria(
                    ProductHallVenue, ProductHallVenue.is_deleted == False
                )
            )
            .options(contains_eager(ProductHall.product_hall_venues))
            .outerjoin(ProductHallVenue)
        )

        result = await db.stream(query)
        return await result.unique().scalar_one_or_none()

    async def filter_halls(
        self,
        db: AsyncSession,
        *,
        sidos: list[str] = None,
        guguns: list[str] = None,
        guest_counts: list[str] = None,
        wedding_types: list[str] = None,
        food_menus: list[str] = None,
        hall_types: list[str] = None,
        hall_styles: list[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductHall]:
        """
        Filter product halls with various criteria
        Optimized using explicit joins and efficient filtering
        """
        query = (
            select(ProductHall)
            .join(
                Product,
                and_(
                    Product.id == ProductHall.product_id,
                    Product.is_deleted == False,
                    Product.available == True,
                ),
            )
            .where(ProductHall.is_deleted == False)
        )

        if sidos:
            sido_likes = [Product.sido.like(f"%{sido}%") for sido in sidos]
            query = query.where(or_(*sido_likes))

        if guguns:
            gugun_likes = [Product.gugun.like(f"%{gugun}%") for gugun in guguns]
            query = query.where(or_(*gugun_likes))

        # 베뉴 관련 필터가 있는 경우 조인
        if any([guest_counts, wedding_types, food_menus, hall_types, hall_styles]):
            query = query.join(
                ProductHallVenue,
                and_(
                    ProductHall.id == ProductHallVenue.product_hall_id,
                    ProductHallVenue.is_deleted == False,
                ),
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
                hall_type_filters = []
                for hall_type in hall_types:
                    hall_type_filters.append(
                        or_(
                            ProductHallVenue.hall_types == hall_type,
                            ProductHallVenue.hall_types.like(f"{hall_type},%"),
                            ProductHallVenue.hall_types.like(f"%,{hall_type},%"),
                            ProductHallVenue.hall_types.like(f"%,{hall_type}"),
                        )
                    )
                if hall_type_filters:
                    query = query.where(or_(*hall_type_filters))

            if hall_styles:
                hall_style_filters = []
                for hall_style in hall_styles:
                    hall_style_filters.append(
                        or_(
                            ProductHallVenue.hall_styles == hall_style,
                            ProductHallVenue.hall_styles.like(f"{hall_style},%"),
                            ProductHallVenue.hall_styles.like(f"%,{hall_style},%"),
                            ProductHallVenue.hall_styles.like(f"%,{hall_style}"),
                        )
                    )
                if hall_style_filters:
                    query = query.where(or_(*hall_style_filters))

        query = query.distinct().offset(skip).limit(limit)

        result = await db.stream(query)
        return await result.scalars().all()

    async def count_filtered_halls(
        self,
        db: AsyncSession,
        *,
        sidos: list[str] = None,
        guguns: list[str] = None,
        guest_counts: list[str] = None,
        wedding_types: list[str] = None,
        food_menus: list[str] = None,
        hall_types: list[str] = None,
        hall_styles: list[str] = None,
    ) -> int:
        """
        Filter product halls count with various criteria
        Same filtering logic as filter_halls but returns count only
        """
        query = (
            select(func.count(ProductHall.id.distinct()))
            .join(
                Product,
                and_(
                    Product.id == ProductHall.product_id,
                    Product.is_deleted == False,
                    Product.available == True,
                ),
            )
            .where(ProductHall.is_deleted == False)
        )

        if sidos:
            sido_likes = [Product.sido.like(f"%{sido}%") for sido in sidos]
            query = query.where(or_(*sido_likes))

        if guguns:
            gugun_likes = [Product.gugun.like(f"%{gugun}%") for gugun in guguns]
            query = query.where(or_(*gugun_likes))

        # 베뉴 관련 필터가 있는 경우 조인
        if any([guest_counts, wedding_types, food_menus, hall_types, hall_styles]):
            query = query.join(
                ProductHallVenue,
                and_(
                    ProductHall.id == ProductHallVenue.product_hall_id,
                    ProductHallVenue.is_deleted == False,
                ),
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
                hall_type_filters = []
                for hall_type in hall_types:
                    hall_type_filters.append(
                        or_(
                            ProductHallVenue.hall_types == hall_type,
                            ProductHallVenue.hall_types.like(f"{hall_type},%"),
                            ProductHallVenue.hall_types.like(f"%,{hall_type},%"),
                            ProductHallVenue.hall_types.like(f"%,{hall_type}"),
                        )
                    )
                if hall_type_filters:
                    query = query.where(or_(*hall_type_filters))

            if hall_styles:
                hall_style_filters = []
                for hall_style in hall_styles:
                    hall_style_filters.append(
                        or_(
                            ProductHallVenue.hall_styles == hall_style,
                            ProductHallVenue.hall_styles.like(f"{hall_style},%"),
                            ProductHallVenue.hall_styles.like(f"%,{hall_style},%"),
                            ProductHallVenue.hall_styles.like(f"%,{hall_style}"),
                        )
                    )
                if hall_style_filters:
                    query = query.where(or_(*hall_style_filters))

        result = await db.stream(query)
        return await result.scalar_one() or 0
