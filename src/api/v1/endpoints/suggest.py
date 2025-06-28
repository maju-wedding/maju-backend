from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import recommended_hall as crud_recommended_hall
from schemes.product_halls import ProductHallSearchRead

router = APIRouter()


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
