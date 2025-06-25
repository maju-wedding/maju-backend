from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_images import ProductImage
from .base import CRUDBase


class CRUDProductImage(CRUDBase[ProductImage, dict[str, Any], dict[str, Any], int]):
    async def get_by_product(
        self, db: AsyncSession, *, product_id: int
    ) -> list[ProductImage]:
        """Get all images by product ID"""
        query = (
            select(ProductImage)
            .where(
                and_(
                    ProductImage.product_id == product_id,
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(ProductImage.order)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_venue(
        self, db: AsyncSession, *, venue_id: int
    ) -> list[ProductImage]:
        """Get venue-specific images by venue ID"""
        query = (
            select(ProductImage)
            .where(
                and_(
                    ProductImage.product_venue_id == venue_id,
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(ProductImage.order)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_product_and_type(
        self, db: AsyncSession, *, product_id: int, image_type: str
    ) -> list[ProductImage]:
        """Get images by product ID and image type"""
        query = (
            select(ProductImage)
            .where(
                and_(
                    ProductImage.product_id == product_id,
                    ProductImage.image_type == image_type,
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(ProductImage.order)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_venue_amenities_images_for_venues(
        self, db: AsyncSession, *, product_id: int, venue_ids: list[int]
    ) -> dict[int, list[ProductImage]]:
        """
        특정 venue들의 이미지와 공통 이미지를 가져와서 venue별로 그룹핑
        venue_id가 None인 이미지는 모든 venue에 공통으로 적용
        """
        # 1. venue별 전용 이미지 조회
        venue_specific_query = (
            select(ProductImage)
            .where(
                and_(
                    ProductImage.product_id == product_id,
                    ProductImage.product_venue_id.in_(venue_ids),
                    ProductImage.image_type.in_(["신부대기실", "폐백실", "연회장"]),
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(
                ProductImage.product_venue_id,
                ProductImage.image_type,
                ProductImage.order,
            )
        )

        venue_specific_result = await db.stream(venue_specific_query)
        venue_specific_images = await venue_specific_result.scalars().all()

        # 2. 공통 이미지 조회 (product_venue_id가 None인 것들)
        common_query = (
            select(ProductImage)
            .where(
                and_(
                    ProductImage.product_id == product_id,
                    ProductImage.product_venue_id.is_(None),
                    ProductImage.image_type.in_(["신부대기실", "폐백실", "연회장"]),
                    ProductImage.is_deleted == False,
                )
            )
            .order_by(ProductImage.image_type, ProductImage.order)
        )

        common_result = await db.stream(common_query)
        common_images = await common_result.scalars().all()

        # 3. venue별로 이미지 그룹핑
        venue_images = {}

        # 먼저 모든 venue에 공통 이미지 할당
        for venue_id in venue_ids:
            venue_images[venue_id] = list(common_images)

        # venue 전용 이미지가 있는 경우 해당 타입의 공통 이미지를 대체
        for image in venue_specific_images:
            venue_id = image.product_venue_id
            if venue_id in venue_images:
                # 같은 타입의 공통 이미지 제거
                venue_images[venue_id] = [
                    img
                    for img in venue_images[venue_id]
                    if img.image_type != image.image_type
                ]
                # venue 전용 이미지 추가
                venue_images[venue_id].append(image)

        # 각 venue의 이미지를 타입과 order로 정렬
        for venue_id in venue_images:
            venue_images[venue_id].sort(key=lambda x: (x.image_type, x.order))

        return venue_images
