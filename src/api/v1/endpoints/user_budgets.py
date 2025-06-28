from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user
from core.db import get_session
from crud import category as crud_category
from crud import user_spent as crud_spent
from models import User
from schemes.checklists import CategoryRead
from schemes.user_spents import (
    UserSpentCreate,
    UserSpentWithCategory,
    BudgetDashboard,
    BudgetSummary,
    CategorySpentSummary,
    UserSpentUpdate,
)

router = APIRouter()


@router.get("/summary", response_model=BudgetDashboard)
async def get_budget_dashboard(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """예산 대시보드 정보 조회"""

    # 총 지출 금액 조회
    total_spent = await crud_spent.get_total_spent_by_user(
        db=session,
        user_id=current_user.id,
    )

    # 예산 요약 정보
    remaining_budget = current_user.budget - total_spent
    usage_percentage = (
        (total_spent / current_user.budget * 100) if current_user.budget > 0 else 0
    )

    budget_summary = BudgetSummary(
        total_budget=current_user.budget,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        budget_usage_percentage=min(100, round(usage_percentage, 1)),
    )

    # 카테고리별 지출 요약
    category_spents = await crud_spent.get_spent_by_category(
        db=session,
        user_id=current_user.id,
    )

    category_summaries = []
    for item in category_spents:
        category_summaries.append(
            CategorySpentSummary(
                category=CategoryRead.model_validate(item["category"]),
                total_spent=item["total_spent"],
                spent_count=item["spent_count"],
            )
        )

    return BudgetDashboard(
        budget_summary=budget_summary,
        category_summaries=category_summaries,
    )


@router.post(
    "/spents", response_model=UserSpentWithCategory, status_code=status.HTTP_201_CREATED
)
async def create_user_spent(
    spent_create: UserSpentCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """지출 내역 생성"""
    # 카테고리 존재 여부 확인
    category = await crud_category.get(db=session, id=spent_create.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # 시스템 카테고리가 아닌 경우에만 권한 검증
    if not category.is_system_category and category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to use this category",
        )

    # 지출 금액 검증
    if spent_create.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be negative"
        )

    # 시스템 카테고리인 경우 CRUD에서 자동으로 사용자 카테고리로 변환됨
    spent = await crud_spent.create_spent(
        db=session, user_id=current_user.id, obj_in=spent_create
    )

    # 카테고리 정보와 함께 반환
    spent_with_category = await crud_spent.get_user_spent_with_category(
        db=session, spent_id=spent.id, user_id=current_user.id
    )

    result = UserSpentWithCategory.model_validate(spent_with_category)
    if spent_with_category.category:
        result.category = CategoryRead.model_validate(spent_with_category.category)

    return result


@router.put("/spents/{spent_id}", response_model=UserSpentWithCategory)
async def update_user_spent(
    spent_id: int = Path(..., description="수정할 지출 ID"),
    spent_update: UserSpentUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """지출 내역 수정"""

    # 지출 내역이 존재하는지 확인
    existing_spent = await crud_spent.get_user_spent_with_category(
        db=session, spent_id=spent_id, user_id=current_user.id
    )

    if not existing_spent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spent record not found"
        )

    # 카테고리 변경이 있는 경우 카테고리 유효성 검증
    if spent_update.category_id is not None:
        category = await crud_category.get(db=session, id=spent_update.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )

        # 시스템 카테고리가 아닌 경우에만 권한 검증
        if not category.is_system_category and category.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this category",
            )

    # 지출 금액 검증 (금액이 제공된 경우)
    if spent_update.amount is not None and spent_update.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be negative"
        )

    # 지출 내역 수정
    updated_spent = await crud_spent.update_spent(
        db=session, spent_id=spent_id, user_id=current_user.id, obj_in=spent_update
    )

    if not updated_spent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update spent record",
        )

    # 카테고리 정보와 함께 반환
    spent_with_category = await crud_spent.get_user_spent_with_category(
        db=session, spent_id=updated_spent.id, user_id=current_user.id
    )

    result = UserSpentWithCategory.model_validate(spent_with_category)
    if spent_with_category.category:
        result.category = CategoryRead.model_validate(spent_with_category.category)

    return result


@router.delete("/spents/{spent_id}", response_model=dict)
async def delete_user_spent(
    spent_id: int = Path(..., description="삭제할 지출 ID"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """지출 내역 삭제 (소프트 삭제)"""

    # 지출 내역 소프트 삭제
    deleted_spent = await crud_spent.soft_delete_spent(
        db=session, spent_id=spent_id, user_id=current_user.id
    )

    if not deleted_spent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spent record not found"
        )

    return {
        "status": "success",
        "message": "Spent record deleted successfully",
        "deleted_id": spent_id,
    }


@router.get("/spents", response_model=list[UserSpentWithCategory])
async def list_user_spents(
    category_id: int | None = Query(None, description="카테고리 ID로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 지출 내역 목록 조회"""
    spents = await crud_spent.get_by_user(
        db=session,
        user_id=current_user.id,
        category_id=category_id,
        skip=skip,
        limit=limit,
    )

    result = []
    for spent in spents:
        spent_with_category = UserSpentWithCategory.model_validate(spent)
        if spent.category:
            spent_with_category.category = CategoryRead.model_validate(spent.category)
        result.append(spent_with_category)

    return result
