from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from models import User, Checklist, ChecklistCategory
from schemes.checklists import (
    ChecklistRead,
    ChecklistCreate,
    ChecklistOrderUpdate,
    ChecklistUpdate,
    SuggestChecklistRead,
)
from schemes.common import ResponseWithStatusMessage

router = APIRouter()


@router.get("/system", response_model=list[SuggestChecklistRead])
async def list_system_checklists(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 목록 조회"""
    query = (
        select(Checklist)
        .where(
            and_(Checklist.is_system_checklist == True, Checklist.is_deleted == False)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await session.stream(query)
    checklists = await result.scalars().all()
    return [SuggestChecklistRead.model_validate(checklist) for checklist in checklists]


@router.get("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def get_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 제공 기본 체크리스트 항목 조회"""
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_id,
            Checklist.is_deleted == False,
            Checklist.is_system_checklist == True,
        )
    )
    result = await session.stream(query)
    system_checklist = await result.scalar_one_or_none()

    if not system_checklist:
        raise HTTPException(status_code=404, detail="Suggest checklist not found")

    return SuggestChecklistRead.model_validate(system_checklist)


@router.post("/system", response_model=SuggestChecklistRead)
async def create_system_checklist(
    system_checklist_create: ChecklistCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 생성"""
    query = select(ChecklistCategory).where(
        and_(
            ChecklistCategory.id == system_checklist_create.checklist_category_id,
            ChecklistCategory.is_system_category == True,
            ChecklistCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    system_checklist_category = await result.scalar_one_or_none()

    if not system_checklist_category:
        raise HTTPException(
            status_code=400,
            detail="System checklist category not found",
        )

    checklist = Checklist(
        title=system_checklist_create.title,
        description=system_checklist_create.description,
        checklist_category_id=system_checklist_create.checklist_category_id,
        is_system_checklist=True,
    )
    session.add(checklist)
    await session.commit()
    await session.refresh(checklist)
    return SuggestChecklistRead.model_validate(checklist)


@router.put("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def update_system_checklist(
    checklist_id: int = Path(...),
    system_checklist_update: ChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 업데이트"""
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_id,
            Checklist.is_deleted == False,
            Checklist.is_system_checklist == True,
        )
    )
    result = await session.stream(query)
    system_checklist = await result.scalar_one_or_none()

    if not system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    if system_checklist_update.checklist_category_id:
        query = select(ChecklistCategory).where(
            and_(
                ChecklistCategory.id == system_checklist_update.checklist_category_id,
                ChecklistCategory.is_system_category == True,
                ChecklistCategory.is_deleted == False,
            )
        )
        result = await session.stream(query)
        system_checklist_category = await result.scalar_one_or_none()

        if not system_checklist_category:
            raise HTTPException(
                status_code=400,
                detail="System checklist category not found",
            )

    for field, value in system_checklist_update.model_dump(exclude_unset=True).items():
        setattr(system_checklist, field, value)

    await session.commit()
    await session.refresh(system_checklist)
    return SuggestChecklistRead.model_validate(system_checklist)


@router.delete("/system/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 삭제"""
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_id,
            Checklist.is_deleted == False,
            Checklist.is_system_checklist == True,
        )
    )
    result = await session.stream(query)
    system_checklist = await result.scalar_one_or_none()

    if not system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    system_checklist.is_deleted = True
    await session.commit()
    return ResponseWithStatusMessage(
        status="success", message="Suggest checklist deleted"
    )


@router.get("", response_model=list[ChecklistRead])
async def list_checklists(
    category_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 목록 조회"""
    query = (
        select(Checklist)
        .join(
            ChecklistCategory, Checklist.checklist_category_id == ChecklistCategory.id
        )
        .where(
            and_(
                Checklist.user_id == current_user.id,
                Checklist.is_deleted == False,
            )
        )
    )

    if category_id:
        query = query.where(Checklist.checklist_category_id == category_id)

    query = query.offset(skip).limit(limit)
    result = await session.stream(query)
    checklists = await result.scalars().all()
    return [ChecklistRead.model_validate(checklist) for checklist in checklists]


@router.post("", response_model=list[ChecklistRead])
async def create_checklists(
    checklist_create: ChecklistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 생성"""
    # Get system checklist
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_create.checklist_category_id,
            Checklist.is_system_checklist == True,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    system_checklist = await result.scalar_one_or_none()

    if not system_checklist:
        raise HTTPException(status_code=404, detail="System checklist not found")

    # Get last order
    query = select(func.max(Checklist.global_display_order)).where(
        and_(
            Checklist.user_id == current_user.id,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    last_global_order = await result.scalar_one_or_none() or 0

    query = select(func.max(Checklist.category_display_order)).where(
        and_(
            Checklist.user_id == current_user.id,
            Checklist.checklist_category_id == checklist_create.checklist_category_id,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    last_category_order = await result.scalar_one_or_none() or 0

    # Create user checklist
    checklist = Checklist(
        user_id=current_user.id,
        checklist_category_id=checklist_create.checklist_category_id,
        title=system_checklist.title,
        description=system_checklist.description,
        global_display_order=last_global_order + 1,
        category_display_order=last_category_order + 1,
    )
    session.add(checklist)
    await session.commit()
    await session.refresh(checklist)
    return [ChecklistRead.model_validate(checklist)]


@router.post("/custom", response_model=ChecklistRead)
async def create_custom_checklist(
    checklist: ChecklistCreate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 정의 체크리스트 항목 생성 (추천에서 가져오지 않는 경우)"""
    query = select(ChecklistCategory).where(
        and_(
            ChecklistCategory.id == checklist.checklist_category_id,
            ChecklistCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    checklist_category = await result.scalar_one_or_none()

    if not checklist_category:
        raise HTTPException(
            status_code=400,
            detail="Checklist category not found",
        )

    if (
        not checklist_category.is_system_category
        and checklist_category.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create checklist in this category",
        )

    # Get last global display order
    query = (
        select(Checklist)
        .where(
            and_(
                Checklist.user_id == current_user.id,
                Checklist.is_deleted == False,
            )
        )
        .order_by(Checklist.global_display_order.desc())
        .limit(1)
    )
    result = await session.stream(query)
    last_global_display_order_checklist = await result.scalar_one_or_none()

    # Get last category display order
    query = (
        select(Checklist)
        .where(
            and_(
                Checklist.user_id == current_user.id,
                Checklist.checklist_category_id == checklist.checklist_category_id,
                Checklist.is_deleted == False,
            )
        )
        .order_by(Checklist.category_display_order.desc())
        .limit(1)
    )
    result = await session.stream(query)
    last_category_display_order_checklist = await result.scalar_one_or_none()

    # Create checklist
    new_checklist = Checklist(
        title=checklist.title,
        description=checklist.description,
        checklist_category_id=checklist.checklist_category_id,
        user_id=current_user.id,
        is_system_checklist=False,
        global_display_order=(
            last_global_display_order_checklist.global_display_order + 1
            if last_global_display_order_checklist
            else 0
        ),
        category_display_order=(
            last_category_display_order_checklist.category_display_order + 1
            if last_category_display_order_checklist
            else 0
        ),
    )
    session.add(new_checklist)
    await session.commit()
    await session.refresh(new_checklist)
    return ChecklistRead.model_validate(new_checklist)


@router.put("/reorder", response_model=list[ChecklistRead])
async def update_checklists_order(
    checklist_order_data: list[ChecklistOrderUpdate] = Body(...),
    is_global_order: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 순서 업데이트"""
    checklist_ids = [item.id for item in checklist_order_data]
    query = select(Checklist).where(
        and_(
            Checklist.id.in_(checklist_ids),
            Checklist.user_id == current_user.id,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    checklists = await result.scalars().all()

    for checklist in checklists:
        if checklist.user_id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Checklists are not owned by the user",
            )

    # Update display orders
    results = []
    for item in checklist_order_data:
        query = select(Checklist).where(
            and_(
                Checklist.id == item.id,
                Checklist.is_deleted == False,
            )
        )
        result = await session.stream(query)
        existing_item = await result.scalar_one_or_none()

        if existing_item:
            if is_global_order:
                existing_item.global_display_order = item.display_order
            else:
                existing_item.category_display_order = item.display_order
            results.append(existing_item)

    await session.commit()
    return [ChecklistRead.model_validate(checklist) for checklist in results]


@router.put("/{checklist_id}", response_model=ChecklistRead)
async def update_checklist(
    checklist_id: int = Path(...),
    checklist_update: ChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 수정"""
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_id,
            Checklist.user_id == current_user.id,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    checklist = await result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    for field, value in checklist_update.model_dump(exclude_unset=True).items():
        setattr(checklist, field, value)

    await session.commit()
    await session.refresh(checklist)
    return ChecklistRead.model_validate(checklist)


@router.delete("/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 삭제"""
    query = select(Checklist).where(
        and_(
            Checklist.id == checklist_id,
            Checklist.user_id == current_user.id,
            Checklist.is_deleted == False,
        )
    )
    result = await session.stream(query)
    checklist = await result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    checklist.is_deleted = True
    await session.commit()
    return ResponseWithStatusMessage(message="Checklist deleted successfully")
