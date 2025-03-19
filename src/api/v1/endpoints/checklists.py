from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from cruds.checklists import (
    checklists_crud,
    checklist_categories_crud,
)
from models import User
from models.checklist_categories import ChecklistCategory
from models.checklists import Checklist
from schemes.checklists import (
    ChecklistRead,
    ChecklistCreate,
    ChecklistOrderUpdate,
    ChecklistUpdate,
    SuggestChecklistRead,
    InternalChecklistCreate,
)
from schemes.common import ResponseWithStatusMessage

router = APIRouter()


@router.get("/system", response_model=list[SuggestChecklistRead])
async def list_system_checklists(
    checklist_category_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    query = {"is_system_checklist": True, "is_deleted": False}

    if checklist_category_id:
        query["checklist_category_id"] = checklist_category_id

    system_checklists = await checklists_crud.get_multi(
        session,
        offset=offset,
        limit=limit,
        schema_to_select=ChecklistRead,
        return_as_model=True,
        sort_columns="global_display_order",
        sort_orders="asc",
        **query,
    )

    return system_checklists.get("data")


@router.get("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def get_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 제공 기본 체크리스트 항목 조회"""
    system_checklist = await checklists_crud.get(
        session,
        id=checklist_id,
        is_deleted=False,
        is_system_checklist=True,
        return_as_model=True,
        schema_to_select=SuggestChecklistRead,
    )

    if not system_checklist:
        raise HTTPException(status_code=404, detail="Suggest checklist not found")

    return system_checklist


@router.post("/system", response_model=SuggestChecklistRead)
async def create_system_checklist(
    system_checklist_create: ChecklistCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 생성"""
    system_checklist_category = await checklist_categories_crud.get(
        session,
        id=system_checklist_create.checklist_category_id,
        is_system_category=True,
        is_deleted=False,
    )

    if not system_checklist_category:
        raise HTTPException(
            status_code=400,
            detail="System checklist category not found",
        )

    return await checklists_crud.create(
        session,
        InternalChecklistCreate(
            title=system_checklist_create.title,
            description=system_checklist_create.description,
            checklist_category_id=system_checklist_create.checklist_category_id,
            is_system_checklist=True,
        ),
    )


@router.put("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def update_system_checklist(
    checklist_id: int = Path(...),
    system_checklist_update: ChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 업데이트"""
    system_checklist = await checklists_crud.get(
        session,
        id=checklist_id,
        is_deleted=False,
        is_system_checklist=True,
    )

    if not system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    if system_checklist_update.checklist_category_id:
        system_checklist_category = await checklist_categories_crud.get(
            session,
            id=system_checklist_update.checklist_category_id,
            is_system_category=True,
            is_deleted=False,
        )

        if not system_checklist_category:
            raise HTTPException(
                status_code=400,
                detail="System checklist category not found",
            )

    return await checklists_crud.update(
        session,
        system_checklist_update,
        id=checklist_id,
        is_system_checklist=True,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=SuggestChecklistRead,
    )


@router.delete("/system/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 삭제"""
    system_checklist = await checklists_crud.get(
        session,
        id=checklist_id,
        is_deleted=False,
        is_system_checklist=True,
    )

    if not system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    await checklists_crud.delete(
        session,
        id=checklist_id,
        is_system_checklist=True,
        is_deleted=False,
    )

    return ResponseWithStatusMessage(
        status="success", message="Suggest checklist deleted"
    )


@router.get("", response_model=list[ChecklistRead])
async def list_checklists(
    checklist_category_id: int | None = Query(None),
    contains_completed: bool = Query(True),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 목록 조회 (카테고리별, 완료 상태별 필터링 가능)"""
    query = {"user_id": current_user.id, "is_deleted": False}
    sort_column = "global_display_order"

    # 카테고리 필터링
    if checklist_category_id is not None:
        query["checklist_category_id"] = checklist_category_id
        sort_column = "category_display_order"

    # 완료된 항목만 조회
    if not contains_completed:
        query["is_completed"] = False

    checklist = await checklists_crud.get_multi_joined(
        session,
        schema_to_select=ChecklistRead,
        return_as_model=True,
        join_model=ChecklistCategory,
        join_prefix="checklist_category_",
        sort_columns=sort_column,
        sort_orders="asc",
        **query,
    )

    return checklist.get("data")


@router.post("", response_model=list[ChecklistRead])
async def create_checklists(
    system_checklist_ids: list[int] = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """시스템 제공 기본 체크리스트 항목들을 사용자 체크리스트로 생성"""
    system_checklist_ids = list(set(system_checklist_ids))

    # 선택된 기본 체크리스트 항목들 조회
    results = await checklists_crud.get_multi(
        session,
        id__in=system_checklist_ids,
        is_system_checklist=True,
        is_deleted=False,
        schema_to_select=Checklist,
        return_as_model=True,
    )

    system_checklists = results.get("data")

    if not system_checklists:
        raise HTTPException(status_code=404, detail="System checklists not found")

    # 선택한 항목들을 유저 체크리스트로 변환
    checklist_items = []
    for system_checklist in system_checklists:
        checklist_item = Checklist(
            title=system_checklist.title,
            description=system_checklist.description,
            user_id=current_user.id,
            checklist_category_id=system_checklist.checklist_category_id,
        )
        checklist_items.append(checklist_item)

        await checklists_crud.create(
            session,
            checklist_item,
        )

    return checklist_items


@router.post("/custom", response_model=ChecklistRead)
async def create_custom_checklist(
    checklist: ChecklistCreate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 정의 체크리스트 항목 생성 (추천에서 가져오지 않는 경우)"""
    checklist_category = await checklist_categories_crud.get(
        session,
        id=checklist.checklist_category_id,
        is_deleted=False,
        schema_to_select=ChecklistCategory,
        return_as_model=True,
    )

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

    return await checklists_crud.create(
        session,
        InternalChecklistCreate(
            title=checklist.title,
            description=checklist.description,
            checklist_category_id=checklist.checklist_category_id,
            user_id=current_user.id,
            is_system_checklist=False,
        ),
    )


@router.put("/reorder", response_model=list[ChecklistRead])
async def update_checklists_order(
    checklist_order_data: list[ChecklistOrderUpdate] = Body(...),
    is_global_order: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 순서 업데이트"""
    checklist_ids = [item.id for item in checklist_order_data]
    results = await checklists_crud.get_multi(
        session,
        id__in=checklist_ids,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=Checklist,
    )

    checklists = results.get("data")

    for checklist in checklists:
        if checklist.user_id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Checklists are not owned by the user",
            )

    # 각 체크리스트 항목의 순서 업데이트
    results = []
    for item in checklist_order_data:
        existing_item = await checklists_crud.get(session, id=item.id, is_deleted=False)
        update_data = {
            (
                "global_display_order" if is_global_order else "category_display_order"
            ): item.display_order
        }
        updated_item = await checklists_crud.update(
            session,
            id=existing_item.id,
            **update_data,
            return_as_model=True,
            schema_to_select=Checklist,
        )
        results.append(updated_item)

    return results


@router.put("/{checklist_id}", response_model=ChecklistRead)
async def update_checklist(
    checklist_id: int = Path(...),
    checklist_update: ChecklistUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 업데이트 (완료/미완료 상태 포함)"""
    existing_checklist = await checklists_crud.get(
        session,
        id=checklist_id,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=Checklist,
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="Checklist not found",
        )

    if existing_checklist.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to update this checklist",
        )

    update_data = checklist_update.model_dump(exclude_none=True)

    if (
        "is_completed" in update_data
        and update_data["is_completed"] != existing_checklist.is_completed
    ):
        update_data["completed_datetime"] = (
            datetime.now() if update_data["is_completed"] else None
        )

    return await checklists_crud.update(
        session,
        update_data,
        id=existing_checklist.id,
        return_as_model=True,
        schema_to_select=Checklist,
    )


@router.delete("/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_checklist(
    checklist_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing_checklist = await checklists_crud.get(
        session,
        id=checklist_id,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=Checklist,
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="해당 체크리스트를 찾을 수 없거나 사용자의 것이 아닙니다",
        )

    await checklists_crud.delete(
        session,
        id=existing_checklist.id,
        user_id=current_user.id,
        is_deleted=True,
    )

    return ResponseWithStatusMessage(status="success", message="Checklist deleted")
