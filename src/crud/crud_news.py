from typing import Sequence, Any

from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import and_

from models import NewsItem, NewsCategory
from schemes.news import (
    NewsItemCreate,
    NewsItemUpdate,
    NewsCategoryCreate,
    NewsCategoryUpdate,
)
from .base import CRUDBase


class CRUDNewsCategory(
    CRUDBase[NewsCategory, NewsCategoryCreate, NewsCategoryUpdate, int]
):
    async def get_categories(
        self, db: AsyncSession
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """뉴스 개수와 함께 카테고리 조회"""
        query = (
            select(NewsCategory)
            .where(NewsCategory.is_deleted == False)
            .order_by(NewsCategory.created_datetime.desc())
        )
        result = await db.stream(query)
        return await result.scalars().all()


class CRUDNewsItem(CRUDBase[NewsItem, NewsItemCreate, NewsItemUpdate, int]):
    async def get_by_category(
        self, db: AsyncSession, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[NewsItem]:
        """카테고리별 뉴스 조회"""
        query = (
            select(self.model)
            .options(selectinload(self.model.news_category))
            .where(
                and_(
                    self.model.news_category_id == category_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.post_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_latest_news(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """최신 뉴스 조회"""
        query = (
            select(self.model)
            .options(selectinload(self.model.news_category))
            .where(self.model.is_deleted == False)
            .order_by(self.model.post_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()
