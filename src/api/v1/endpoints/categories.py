from fastapi import Depends, Path, HTTPException, Body, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
from core.db import get_session
from crud import category as crud_category
from models import User
from schemes.checklists import (
    CategoryRead,
    CategoryUpdate,
    CategoryCreate,
    CategoryReadWithChecklist,
)
from schemes.common import ResponseWithStatusMessage

router = APIRouter()


@router.get(
    "/system/summary",
    response_model=list[CategoryReadWithChecklist],
)
async def list_system_categories_summary(
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 목록 조회 (체크리스트 포함)"""
    categories_with_checklists = (
        await crud_category.get_system_categories_with_checklists(db=session)
    )
    return categories_with_checklists


@router.get(
    "/system",
    response_model=list[CategoryRead],
)
async def list_system_categories(
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 목록 조회"""
    categories_with_counts = await crud_category.get_categories_with_checklist_count(
        db=session, system_only=True
    )

    result = []
    for category, count in categories_with_counts:
        result.append(
            CategoryRead(
                id=category.id,
                display_name=category.display_name,
                user_id=category.user_id,
                is_system_category=category.is_system_category,
                checklists_count=count,
            )
        )

    return result


@router.get("/system/{category_id}", response_model=CategoryRead)
async def get_system_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 상세 조회"""
    category, checklist_count = await crud_category.get_category_with_checklist_count(
        db=session, category_id=category_id
    )

    if not category or not category.is_system_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    return CategoryRead(
        id=category.id,
        display_name=category.display_name,
        user_id=category.user_id,
        is_system_category=category.is_system_category,
        checklists_count=checklist_count,
    )


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 목록 조회"""
    categories_with_counts = (
        await crud_category.get_user_categories_with_checklist_count(
            db=session, user_id=current_user.id
        )
    )
    result = []
    for category, count in categories_with_counts:
        result.append(
            CategoryRead(
                id=category.id,
                display_name=category.display_name,
                user_id=category.user_id,
                is_system_category=category.is_system_category,
                checklists_count=count,
            )
        )

    return result


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 상세 조회"""
    category, checklist_count = (
        await crud_category.get_user_category_with_checklist_count(
            db=session, category_id=category_id, user_id=current_user.id
        )
    )

    if not category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    return CategoryRead(
        id=category.id,
        display_name=category.display_name,
        user_id=category.user_id,
        is_system_category=category.is_system_category,
        checklists_count=checklist_count,
    )


@router.post("", response_model=CategoryRead)
async def create_category(
    category_in: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 생성"""
    category = await crud_category.create_user_category(
        db=session,
        display_name=category_in.display_name,
        user_id=current_user.id,
        icon_url=category_in.icon_url,
    )

    return CategoryRead.model_validate(category)


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int = Path(...),
    category_in: CategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 수정"""
    category = await crud_category.get_user_category(
        db=session, category_id=category_id, user_id=current_user.id
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    updated_category = await crud_category.update(
        db=session, db_obj=category, obj_in=category_in
    )

    return CategoryRead.model_validate(updated_category)


@router.delete("/{category_id}", response_model=ResponseWithStatusMessage)
async def delete_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 삭제"""
    category = await crud_category.get_user_category(
        db=session, category_id=category_id, user_id=current_user.id
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await crud_category.soft_delete_with_checklists(db=session, category_id=category_id)

    return ResponseWithStatusMessage(
        status="success", message="Category deleted successfully"
    )
