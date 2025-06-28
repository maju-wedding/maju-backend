from typing import List, Optional

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.product_halls import ProductHall
from models.suggest_halls import RecommendedHall
from schemes.suggest_halls import RecommendedHallCreate, RecommendedHallUpdate


class CRUDRecommendedHall(
    CRUDBase[RecommendedHall, RecommendedHallCreate, RecommendedHallUpdate, int]
):

    async def get_active_recommendations(
        self, db: AsyncSession, skip: int = 0, limit: int = 10
    ) -> List[RecommendedHall]:
        """활성화된 추천 웨딩홀 목록 조회 (순서대로)"""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.product_hall).selectinload(ProductHall.product)
            )
            .where(and_(self.model.is_deleted == False, self.model.is_active == True))
            .order_by(self.model.recommendation_order.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_all_recommendations(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[RecommendedHall]:
        """모든 추천 웨딩홀 목록 조회 (관리자용)"""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.product_hall).selectinload(ProductHall.product)
            )
            .where(self.model.is_deleted == False)
            .order_by(self.model.recommendation_order.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_product_hall_id(
        self, db: AsyncSession, product_hall_id: int
    ) -> Optional[RecommendedHall]:
        """특정 웨딩홀의 추천 정보 조회"""
        query = select(self.model).where(
            and_(
                self.model.product_hall_id == product_hall_id,
                self.model.is_deleted == False,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_next_order(self, db: AsyncSession) -> int:
        """다음 추천 순서 번호 조회"""
        query = select(func.max(self.model.recommendation_order)).where(
            self.model.is_deleted == False
        )
        result = await db.execute(query)
        max_order = result.scalar()
        return (max_order or 0) + 1

    async def update_orders(self, db: AsyncSession, order_updates: List[dict]) -> bool:
        """여러 추천 웨딩홀의 순서 한번에 업데이트"""
        try:
            for order_update in order_updates:
                await db.execute(
                    update(self.model)
                    .where(
                        and_(
                            self.model.id == order_update["id"],
                            self.model.is_deleted == False,
                        )
                    )
                    .values(recommendation_order=order_update["recommendation_order"])
                )
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False

    async def count_active_recommendations(self, db: AsyncSession) -> int:
        """활성화된 추천 웨딩홀 개수"""
        query = select(func.count(self.model.id)).where(
            and_(self.model.is_deleted == False, self.model.is_active == True)
        )
        result = await db.execute(query)
        return result.scalar()

    async def soft_delete(
        self, db: AsyncSession, *, id: int
    ) -> Optional[RecommendedHall]:
        """추천 웨딩홀 소프트 삭제"""
        db_obj = await self.get(db=db, id=id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.deleted_datetime = func.now()
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj
