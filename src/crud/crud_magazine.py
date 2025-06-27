from typing import Any, Sequence

from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from models.magazines import Magazine
from schemes.magazines import MagazineCreate, MagazineUpdate
from .base import CRUDBase


class CRUDMagazine(CRUDBase[Magazine, MagazineCreate, MagazineUpdate, int]):
    async def get_published_magazines(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """발행된 매거진 목록 조회"""
        query = (
            select(self.model)
            .where(self.model.is_deleted == False)
            .order_by(self.model.created_datetime.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()
