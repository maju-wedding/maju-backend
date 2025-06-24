from collections.abc import Sequence

from sqlalchemy import and_, select, or_, BinaryExpression
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.sql.expression import Select

from models.product_hall_venues import ProductHallVenue
from models.product_halls import ProductHall
from models.product_images import ProductImage
from models.products import Product
from schemes.products import ProductCreate, ProductUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate, int]):
    async def get_by_category(
        self, db: AsyncSession, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Product]:
        """Get products by category ID"""
        query: Select[tuple[Product]] = (
            select(Product)
            .where(
                and_(
                    Product.product_category_id == category_id,
                    Product.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_location(
        self,
        db: AsyncSession,
        *,
        sidos: list[str] = None,
        guguns: list[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """Get products by location (sido/gugun)"""
        query: Select[tuple[Product]] = select(Product).where(
            Product.is_deleted == False
        )

        if sidos:
            query = query.where(Product.sido.in_(sidos))

        if guguns:
            query = query.where(Product.gugun.in_(guguns))

        query = query.offset(skip).limit(limit)
        result = await db.stream(query)
        return await result.scalars().all()

    async def search_products(
        self, db: AsyncSession, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Product]:
        """Search products by name or other fields"""
        query: Select[tuple[Product]] = (
            select(Product)
            .where(
                and_(
                    or_(
                        Product.name.ilike(f"%{search_term}%"),
                        Product.description.ilike(f"%{search_term}%"),
                        Product.address.ilike(f"%{search_term}%"),
                        Product.hashtag.ilike(f"%{search_term}%"),
                    ),
                    Product.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_with_details(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        load_images: bool = True,
        load_hall: bool = False,
    ) -> Product | None:
        """
        Get product with related details loaded
        Optimized version using with_loader_criteria for filtering at query level
        """
        # 기본 쿼리
        query: Select[tuple[Product]] = select(Product).where(
            and_(
                Product.id == product_id,
                Product.is_deleted == False,
            )
        )

        # 이미지 로딩 - 최적화된 쿼리
        if load_images:
            # 이미지에 대한 필터를 적용한 로더 옵션
            image_criteria: BinaryExpression[bool] = ProductImage.is_deleted == False
            query = query.options(with_loader_criteria(ProductImage, image_criteria))
            query = query.options(selectinload(Product.images))

        # 홀 데이터 로딩 - 최적화된 쿼리
        if load_hall:
            # 홀 베뉴에 대한 필터를 적용한 로더 옵션
            venue_criteria: BinaryExpression[bool] = (
                ProductHallVenue.is_deleted == False
            )
            query = query.options(
                with_loader_criteria(ProductHallVenue, venue_criteria)
            )
            query = query.options(
                selectinload(Product.product_hall).selectinload(
                    ProductHall.product_hall_venues
                )
            )

        # 결과 조회
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def add_image(
        self, db: AsyncSession, *, product_id: int, image_url: str, order: int = 0
    ) -> ProductImage | None:
        """Add an image to a product"""
        # Check if product exists
        product = await self.get(db, id=product_id)
        if not product:
            return None

        # Create image
        image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            order=order,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    async def get_with_images_and_hall_using_joins(
        self, db: AsyncSession, *, product_id: int
    ) -> Product | None:
        """
        Get product with images and hall data using explicit joins
        This is the most optimized approach for complex queries
        """
        query: Select[tuple[Product]] = (
            select(Product)
            .where(and_(Product.id == product_id, Product.is_deleted == False))
            .options(
                with_loader_criteria(ProductImage, ProductImage.is_deleted == False),
                with_loader_criteria(
                    ProductHallVenue, ProductHallVenue.is_deleted == False
                ),
                selectinload(Product.images),
                selectinload(Product.product_hall)
                .selectinload(ProductHall.product_hall_venues)
                .selectinload(ProductHallVenue.images),  # 이제 작동함!
            )
        )

        result = await db.stream(query)
        return await result.scalar_one_or_none()
