from fastapi import Depends, Path, HTTPException, Body, APIRouter
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_admin, get_current_user
from core.db import get_session
from models import User, Checklist
from models.checklist_categories import ChecklistCategory
from schemes.checklists import (
    ChecklistCategoryRead,
    ChecklistCategoryCreateBySystem,
    ChecklistCategoryUpdate,
    ChecklistCategoryCreate,
    ChecklistCategoryReadWithChecklist,
)
from schemes.common import ResponseWithStatusMessage

router = APIRouter()


@router.get(
    "/system/summary",
    response_model=list[ChecklistCategoryReadWithChecklist],
)
async def list_system_checklist_categories_summary(
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 목록 조회"""
    query = (
        select(ChecklistCategory, Checklist)
        .outerjoin(Checklist, Checklist.checklist_category_id == ChecklistCategory.id)
        .where(
            and_(
                ChecklistCategory.is_system_category == True,
                ChecklistCategory.is_deleted == False,
            )
        )
        .order_by(ChecklistCategory.id)
    )

    result = await session.stream(query)
    rows = await result.all()
    categories = {}

    for row in rows:
        category: ChecklistCategory = row.ChecklistCategory
        checklist: Checklist = row.Checklist

        if category.id not in categories:
            categories[category.id] = {
                "id": category.id,
                "display_name": category.display_name,
                "user_id": category.user_id,
                "is_system_category": category.is_system_category,
                "checklists": [],
            }

        if checklist:
            categories[category.id]["checklists"].append(
                {
                    "id": checklist.id,
                    "title": checklist.title,
                    "description": checklist.description,
                    "global_display_order": checklist.global_display_order,
                }
            )

    return list(categories.values())


@router.get(
    "/system",
    response_model=list[ChecklistCategoryRead],
)
async def list_system_checklist_categories(
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 목록 조회"""
    query = (
        select(ChecklistCategory, Checklist)
        .outerjoin(Checklist, Checklist.checklist_category_id == ChecklistCategory.id)
        .where(
            and_(
                ChecklistCategory.is_system_category == True,
                ChecklistCategory.is_deleted == False,
            )
        )
        .order_by(ChecklistCategory.id)
    )

    result = await session.stream(query)
    rows = await result.all()
    categories = {}

    for row in rows:
        category: ChecklistCategory = row.ChecklistCategory
        checklist: Checklist = row.Checklist

        if category.id not in categories:
            categories[category.id] = {
                "id": category.id,
                "display_name": category.display_name,
                "user_id": category.user_id,
                "is_system_category": category.is_system_category,
                "checklists_count": 0,
            }

        if checklist:
            categories[category.id]["checklists_count"] += 1

    return list(categories.values())


@router.get("/system/{category_id}", response_model=ChecklistCategoryRead)
async def get_system_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 상세 조회"""
    query = (
        select(ChecklistCategory, Checklist)
        .outerjoin(Checklist, Checklist.checklist_category_id == ChecklistCategory.id)
        .where(
            and_(
                ChecklistCategory.id == category_id,
                ChecklistCategory.is_deleted == False,
            )
        )
    )

    result = await session.stream(query)
    rows = await result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    category: ChecklistCategory = rows[0].ChecklistCategory
    checklists = [row.Checklist for row in rows if row.Checklist]

    return {
        "id": category.id,
        "display_name": category.display_name,
        "user_id": category.user_id,
        "is_system_category": category.is_system_category,
        "checklists_count": len(checklists),
    }


@router.post("/system", response_model=ChecklistCategory)
async def create_system_checklist_category(
    checklist_category_create: ChecklistCategoryCreateBySystem = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 생성"""
    category = ChecklistCategory(
        display_name=checklist_category_create.display_name,
        is_system_category=True,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)

    return category


@router.put("/system/{category_id}", response_model=ChecklistCategory)
async def update_system_checklist_category(
    category_id: int = Path(...),
    checklist_category_update: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 업데이트"""
    query = select(ChecklistCategory).where(
        and_(ChecklistCategory.id == category_id, ChecklistCategory.is_deleted == False)
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    if not category.is_system_category:
        raise HTTPException(
            status_code=400, detail="Only system categories can be updated"
        )

    for field, value in checklist_category_update.model_dump(
        exclude_unset=True
    ).items():
        setattr(category, field, value)

    await session.commit()
    await session.refresh(category)

    return category


@router.delete(
    "/system/{category_id}",
    response_model=ResponseWithStatusMessage,
)
async def delete_system_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 삭제"""
    query = select(ChecklistCategory).where(
        and_(ChecklistCategory.id == category_id, ChecklistCategory.is_deleted == False)
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    if not category.is_system_category:
        raise HTTPException(
            status_code=400, detail="Only system categories can be deleted"
        )

    category.is_deleted = True
    await session.commit()

    return ResponseWithStatusMessage(message="Checklist category deleted")


@router.get("", response_model=list[ChecklistCategoryRead])
async def list_checklist_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 목록 조회"""
    query = (
        select(ChecklistCategory)
        .where(
            and_(
                ChecklistCategory.is_deleted == False,
                ChecklistCategory.user_id == current_user.id,
            )
        )
        .order_by(ChecklistCategory.id)
    )

    result = await session.stream(query)
    categories = await result.scalars().all()

    return [ChecklistCategoryRead.model_validate(category) for category in categories]


@router.get("/{category_id}", response_model=ChecklistCategoryRead)
async def get_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 상세 조회"""
    query = (
        select(ChecklistCategory, func.count(Checklist.id).label("checklist_count"))
        .outerjoin(Checklist, Checklist.checklist_category_id == ChecklistCategory.id)
        .where(
            and_(
                ChecklistCategory.id == category_id,
                ChecklistCategory.user_id == current_user.id,
                ChecklistCategory.is_deleted == False,
            )
        )
        .group_by(ChecklistCategory.id)
    )

    result = await session.stream(query)
    row = await result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    category, checklist_count = row
    return {
        "id": category.id,
        "display_name": category.display_name,
        "user_id": category.user_id,
        "is_system_category": category.is_system_category,
        "checklist_count": checklist_count,
    }


@router.post("", response_model=ChecklistCategoryRead)
async def create_checklist_category(
    category_in: ChecklistCategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 생성"""
    category = ChecklistCategory(
        **category_in.model_dump(), user_id=current_user.id, is_system_category=False
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)

    return ChecklistCategoryRead.model_validate(category)


@router.put("/{category_id}", response_model=ChecklistCategoryRead)
async def update_checklist_category(
    category_id: int = Path(...),
    category_in: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 수정"""
    query = select(ChecklistCategory).where(
        and_(
            ChecklistCategory.id == category_id,
            ChecklistCategory.user_id == current_user.id,
            ChecklistCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    for field, value in category_in.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    await session.commit()
    await session.refresh(category)

    return ChecklistCategoryRead.model_validate(category)


@router.delete("/{category_id}", response_model=ResponseWithStatusMessage)
async def delete_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 삭제"""
    query = select(ChecklistCategory).where(
        and_(
            ChecklistCategory.id == category_id,
            ChecklistCategory.user_id == current_user.id,
            ChecklistCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # 관련된 체크리스트도 삭제
    checklist_query = select(Checklist).where(
        Checklist.checklist_category_id == category_id
    )
    checklist_result = await session.stream(checklist_query)
    checklists = await checklist_result.scalars().all()

    for checklist in checklists:
        checklist.is_deleted = True

    category.is_deleted = True
    await session.commit()

    return ResponseWithStatusMessage(message="Category deleted successfully")
