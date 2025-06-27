from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import magazine as crud_magazine
from schemes.magazines import MagazineRead

router = APIRouter()


@router.get("", response_model=list[MagazineRead])
async def list_magazines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """매거진 목록 조회"""
    magazines = await crud_magazine.get_published_magazines(
        db=session, skip=skip, limit=limit
    )
    return magazines


@router.get("/count", response_model=dict)
async def get_magazines_count(
    session: AsyncSession = Depends(get_session),
):
    """매거진 개수 조회"""
    count = await crud_magazine.count_published_magazines(db=session)
    return {"count": count}


@router.get("/{magazine_id}", response_model=MagazineRead)
async def get_magazine(
    magazine_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """매거진 상세 조회"""
    magazine = await crud_magazine.get(db=session, id=magazine_id)

    if not magazine or magazine.is_deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Magazine not found")

    return magazine
