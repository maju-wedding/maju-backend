from typing import List

from sqlalchemy import select, func
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
    async def get_categories_with_count(
        self, db: AsyncSession
    ) -> List[tuple[NewsCategory, int]]:
        """뉴스 개수와 함께 카테고리 조회"""
        query = (
            select(NewsCategory, func.count(NewsItem.id).label("news_count"))
            .outerjoin(
                NewsItem,
                and_(
                    NewsItem.news_category_id == NewsCategory.id,
                    NewsItem.is_deleted == False,
                ),
            )
            .where(NewsCategory.is_deleted == False)
            .group_by(NewsCategory.id)
            .order_by(NewsCategory.created_datetime.desc())
        )
        result = await db.execute(query)
        return result.all()


class CRUDNewsItem(CRUDBase[NewsItem, NewsItemCreate, NewsItemUpdate, int]):
    async def get_by_category(
        self, db: AsyncSession, category_id: int, skip: int = 0, limit: int = 100
    ) -> List[NewsItem]:
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
        result = await db.execute(query)
        return result.scalars().all()

    async def get_latest_news(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[NewsItem]:
        """최신 뉴스 조회"""
        query = (
            select(self.model)
            .options(selectinload(self.model.news_category))
            .where(self.model.is_deleted == False)
            .order_by(self.model.post_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
