
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.suggest_search_keywords import SuggestSearchKeyword
from .base import CRUDBase


class CRUDSuggestSearchKeyword(CRUDBase[SuggestSearchKeyword, dict, dict, int]):
    async def get_by_keyword(
        self, db: AsyncSession, *, keyword: str
    ) -> SuggestSearchKeyword | None:
        """Get a suggest search keyword by keyword text"""
        query = select(SuggestSearchKeyword).where(
            and_(
                SuggestSearchKeyword.keyword == keyword,
                SuggestSearchKeyword.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()
