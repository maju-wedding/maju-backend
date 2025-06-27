from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.magazines import Magazine
from schemes.magazines import MagazineCreate, MagazineUpdate
from .base import CRUDBase


class CRUDMagazine(CRUDBase[Magazine, MagazineCreate, MagazineUpdate, int]):
    async def get_published_magazines(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Magazine]:
        """발행된 매거진 목록 조회"""
        query = (
            select(self.model)
            .where(self.model.is_deleted == False)
            .order_by(self.model.created_datetime.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def count_published_magazines(self, db: AsyncSession) -> int:
        """발행된 매거진 개수"""
        query = select(func.count(self.model.id)).where(self.model.is_deleted == False)
        result = await db.execute(query)
        return result.scalar() or 0
