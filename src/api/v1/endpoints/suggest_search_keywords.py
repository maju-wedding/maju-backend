from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from models import SuggestSearchKeyword

router = APIRouter()


@router.get("")
async def list_suggest_search_keywords(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 목록 조회"""
    query = (
        select(SuggestSearchKeyword)
        .where(SuggestSearchKeyword.is_deleted == False)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(query)
    keywords = result.scalars().all()
    return keywords


@router.get("/{keyword_id}")
async def get_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 상세 조회"""
    query = select(SuggestSearchKeyword).where(
        SuggestSearchKeyword.id == keyword_id,
        SuggestSearchKeyword.is_deleted == False,
    )
    result = await session.execute(query)
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return keyword


@router.post("")
async def create_suggest_search_keyword(
    keyword: str,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 생성"""
    # Check if keyword already exists
    query = select(SuggestSearchKeyword).where(
        SuggestSearchKeyword.keyword == keyword,
        SuggestSearchKeyword.is_deleted == False,
    )
    result = await session.execute(query)
    existing_keyword = result.scalar_one_or_none()

    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # Create keyword
    suggest_keyword = SuggestSearchKeyword(keyword=keyword)
    session.add(suggest_keyword)
    await session.commit()
    await session.refresh(suggest_keyword)
    return suggest_keyword


@router.put("/{keyword_id}")
async def update_suggest_search_keyword(
    keyword_id: int,
    keyword: str,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 수정"""
    query = select(SuggestSearchKeyword).where(
        SuggestSearchKeyword.id == keyword_id,
        SuggestSearchKeyword.is_deleted == False,
    )
    result = await session.execute(query)
    suggest_keyword = result.scalar_one_or_none()

    if not suggest_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Check if new keyword already exists
    query = select(SuggestSearchKeyword).where(
        SuggestSearchKeyword.keyword == keyword,
        SuggestSearchKeyword.id != keyword_id,
        SuggestSearchKeyword.is_deleted == False,
    )
    result = await session.execute(query)
    existing_keyword = result.scalar_one_or_none()

    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    suggest_keyword.keyword = keyword
    await session.commit()
    await session.refresh(suggest_keyword)
    return suggest_keyword


@router.delete("/{keyword_id}")
async def delete_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 삭제"""
    query = select(SuggestSearchKeyword).where(
        SuggestSearchKeyword.id == keyword_id,
        SuggestSearchKeyword.is_deleted == False,
    )
    result = await session.execute(query)
    suggest_keyword = result.scalar_one_or_none()

    if not suggest_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    suggest_keyword.is_deleted = True
    await session.commit()
    return {"message": "Keyword deleted successfully"}
