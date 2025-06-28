from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import recommended_hall as crud_recommended_hall
from crud import suggest_search_keyword as crud_keyword
from schemes.product_halls import ProductHallSearchRead
from schemes.suggest_search_keywords import SuggestSearchKeywordRead

router = APIRouter()


@router.get("/search-keywords", response_model=list[SuggestSearchKeywordRead])
async def list_suggest_search_keywords(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 목록 조회"""
    keywords = await crud_keyword.get_multi(db=session, skip=skip, limit=limit)
    return [SuggestSearchKeywordRead(id=k.id, keyword=k.keyword) for k in keywords]


@router.get("/search-keywords/{keyword_id}", response_model=SuggestSearchKeywordRead)
async def get_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 상세 조회"""
    keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return SuggestSearchKeywordRead(id=keyword.id, keyword=keyword.keyword)


@router.get("/wedding-halls", response_model=list[ProductHallSearchRead])
async def get_recommended_halls(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    """
    추천 웨딩홀 목록 조회

    - 활성화된 추천 웨딩홀만 조회
    - 추천 순서대로 정렬되어 반환
    """

    recommendations = await crud_recommended_hall.get_active_recommendations(
        db=session, skip=skip, limit=limit
    )

    # ProductHallSearchRead 형태로 변환하여 반환
    result = []
    for rec in recommendations:
        if rec.product_hall and rec.product_hall.product:
            hall_data = ProductHallSearchRead(
                id=rec.product_hall.product.id,
                name=rec.product_hall.product.name,
                sido=rec.product_hall.product.sido,
                gugun=rec.product_hall.product.gugun,
                address=rec.product_hall.product.address,
                thumbnail_url=rec.product_hall.product.thumbnail_url or "",
                subway_line=rec.product_hall.product.subway_line,
                subway_name=rec.product_hall.product.subway_name,
            )
            result.append(hall_data)

    return result
