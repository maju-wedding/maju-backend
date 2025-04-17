from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import suggest_search_keyword as crud_keyword
from schemes.suggest_search_keywords import SuggestSearchKeywordRead

router = APIRouter()


@router.get("", response_model=list[SuggestSearchKeywordRead])
async def list_suggest_search_keywords(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 목록 조회"""
    keywords = await crud_keyword.get_multi(db=session, skip=skip, limit=limit)
    return [SuggestSearchKeywordRead(id=k.id, keyword=k.keyword) for k in keywords]


@router.get("/{keyword_id}", response_model=SuggestSearchKeywordRead)
async def get_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 상세 조회"""
    keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return SuggestSearchKeywordRead(id=keyword.id, keyword=keyword.keyword)
