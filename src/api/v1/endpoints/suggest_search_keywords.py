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


@router.post("", response_model=SuggestSearchKeywordRead)
async def create_suggest_search_keyword(
    keyword: str,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 생성"""
    # 이미 존재하는지 확인
    existing_keyword = await crud_keyword.get_by_keyword(db=session, keyword=keyword)

    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # 키워드 생성
    new_keyword = await crud_keyword.create(db=session, obj_in={"keyword": keyword})

    return SuggestSearchKeywordRead(id=new_keyword.id, keyword=new_keyword.keyword)


@router.put("/{keyword_id}", response_model=SuggestSearchKeywordRead)
async def update_suggest_search_keyword(
    keyword_id: int,
    keyword: str,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 수정"""
    existing_keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not existing_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # 중복 확인
    duplicate = await crud_keyword.get_by_keyword(db=session, keyword=keyword)

    if duplicate and duplicate.id != keyword_id:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # 업데이트
    updated_keyword = await crud_keyword.update(
        db=session, db_obj=existing_keyword, obj_in={"keyword": keyword}
    )

    return SuggestSearchKeywordRead(
        id=updated_keyword.id, keyword=updated_keyword.keyword
    )


@router.delete("/{keyword_id}")
async def delete_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
):
    """검색어 추천 삭제"""
    keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await crud_keyword.soft_delete(db=session, id=keyword_id)

    return {"message": "Keyword deleted successfully"}
