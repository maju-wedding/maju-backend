
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_ai_review import ProductAIReview
from .base import CRUDBase


class CRUDProductAIReview(CRUDBase[ProductAIReview, dict, dict, int]):
    async def get_by_product(
        self, db: AsyncSession, *, product_id: int
    ) -> list[ProductAIReview]:
        """Get AI reviews by product ID"""
        query = select(ProductAIReview).where(
            and_(
                ProductAIReview.product_id == product_id,
                ProductAIReview.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_product_and_type(
        self, db: AsyncSession, *, product_id: int, review_type: str
    ) -> ProductAIReview | None:
        """Get AI review by product ID and review type"""
        query = select(ProductAIReview).where(
            and_(
                ProductAIReview.product_id == product_id,
                ProductAIReview.review_type == review_type,
                ProductAIReview.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()
