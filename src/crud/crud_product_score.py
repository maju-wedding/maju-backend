
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_scores import ProductScore
from .base import CRUDBase


class CRUDProductScore(CRUDBase[ProductScore, dict, dict, int]):
    async def get_by_product(
        self, db: AsyncSession, *, product_id: int
    ) -> list[ProductScore]:
        """Get scores by product ID"""
        query = select(ProductScore).where(
            and_(
                ProductScore.product_id == product_id,
                ProductScore.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_product_and_type(
        self, db: AsyncSession, *, product_id: int, score_type: str
    ) -> ProductScore | None:
        """Get score by product ID and score type"""
        query = select(ProductScore).where(
            and_(
                ProductScore.product_id == product_id,
                ProductScore.score_type == score_type,
                ProductScore.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def update_or_create_score(
        self, db: AsyncSession, *, product_id: int, score_type: str, value: float
    ) -> ProductScore:
        """Update or create a score for a product"""
        score = await self.get_by_product_and_type(
            db=db, product_id=product_id, score_type=score_type
        )

        if score:
            # Update existing score
            score.value = value
            db.add(score)
            await db.commit()
            await db.refresh(score)
            return score
        else:
            # Create new score
            new_score = ProductScore(
                product_id=product_id,
                score_type=score_type,
                value=value,
            )
            db.add(new_score)
            await db.commit()
            await db.refresh(new_score)
            return new_score
