from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import news_category as crud_news_category, news_item as crud_news_item
from schemes.news import NewsCategoryRead, NewsItemRead

router = APIRouter()


@router.get("/categories", response_model=list[NewsCategoryRead])
async def list_news_categories(
    session: AsyncSession = Depends(get_session),
):
    """뉴스 카테고리 목록 조회"""
    categories = await crud_news_category.get_categories(db=session)

    result = []
    for category in categories:
        result.append(
            NewsCategoryRead(
                id=category.id,
                display_name=category.display_name,
                created_datetime=category.created_datetime,
            )
        )

    return result


@router.get("/categories/{category_id}", response_model=NewsCategoryRead)
async def get_news_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """뉴스 카테고리 상세 조회"""
    category = await crud_news_category.get(db=session, id=category_id)

    if not category or category.is_deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="News category not found")

    return NewsCategoryRead(
        id=category.id,
        display_name=category.display_name,
        created_datetime=category.created_datetime,
    )


@router.get("", response_model=list[NewsItemRead])
async def list_news_items(
    category_id: int = Query(None, description="카테고리 ID로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """뉴스 아이템 목록 조회"""
    if category_id:
        news_items = await crud_news_item.get_by_category(
            db=session, category_id=category_id, skip=skip, limit=limit
        )
    else:
        news_items = await crud_news_item.get_latest_news(
            db=session, skip=skip, limit=limit
        )

    result = []
    for news_item in news_items:
        news_read = NewsItemRead(
            id=news_item.id,
            news_category_id=news_item.news_category_id,
            title=news_item.title,
            link_url=news_item.link_url,
            post_date=news_item.post_date,
            created_datetime=news_item.created_datetime,
        )

        if news_item.news_category:
            news_read.news_category = NewsCategoryRead(
                id=news_item.news_category.id,
                display_name=news_item.news_category.display_name,
                created_datetime=news_item.news_category.created_datetime,
            )

        result.append(news_read)

    return result


@router.get("/{news_id}", response_model=NewsItemRead)
async def get_news_item(
    news_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """뉴스 아이템 상세 조회"""
    news_item = await crud_news_item.get(db=session, id=news_id)

    if not news_item or news_item.is_deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="News item not found")

    # 카테고리 정보도 함께 로드
    if news_item.news_category_id:
        category = await crud_news_category.get(
            db=session, id=news_item.news_category_id
        )
        if category:
            return NewsItemRead(
                id=news_item.id,
                news_category_id=news_item.news_category_id,
                title=news_item.title,
                link_url=news_item.link_url,
                post_date=news_item.post_date,
                created_datetime=news_item.created_datetime,
                news_category=NewsCategoryRead(
                    id=category.id,
                    display_name=category.display_name,
                    created_datetime=category.created_datetime,
                ),
            )

    return NewsItemRead(
        id=news_item.id,
        news_category_id=news_item.news_category_id,
        title=news_item.title,
        link_url=news_item.link_url,
        post_date=news_item.post_date,
        created_datetime=news_item.created_datetime,
    )
