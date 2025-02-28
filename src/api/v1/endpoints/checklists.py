from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from cruds.checklists import user_checklists_crud, suggest_checklists_crud
from models import User
from models.checklist import (
    UserChecklist,
    SuggestChecklist,
    UserChecklistResponse,
    UserChecklistCreate,
    ChecklistOrderUpdate,
    UserChecklistUpdate,
    SuggestChecklistCreate,
    SuggestChecklistUpdate,
    ChecklistCategory,
    ChecklistCategoryCreate,
    ChecklistCategoryCreateBySystem,
    InternalChecklistCategoryCreate,
    ChecklistCategoryUpdate,
)

router = APIRouter()


@router.get("/system-checklist-categories", response_model=list[ChecklistCategory])
async def list_checklist_categories(
    session: AsyncSession = Depends(get_session),
):
    """체크리스트 카테고리 목록 조회"""
    return await suggest_checklists_crud.get_multi(
        session,
        schema_to_select=ChecklistCategory,
        return_as_model=True,
    )


@router.get(
    "/system-checklist-categories/{category_id}", response_model=ChecklistCategory
)
async def get_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """체크리스트 카테고리 상세 조회"""
    return await suggest_checklists_crud.get(
        session,
        id=category_id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.post("/system-checklist-categories", response_model=ChecklistCategory)
async def create_system_checklist_category(
    checklist_category_create: ChecklistCategoryCreateBySystem = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """체크리스트 카테고리 생성 (시스템 카테고리)"""
    return await suggest_checklists_crud.create(
        session,
        InternalChecklistCategoryCreate(
            display_name=checklist_category_create.display_name,
            is_system_category=True,
            user_id=current_user.id,
        ),
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.put(
    "/system-checklist-categories/{category_id}", response_model=ChecklistCategory
)
async def update_checklist_category(
    category_id: int = Path(...),
    checklist_category_update: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """체크리스트 카테고리 업데이트"""
    return await suggest_checklists_crud.update(
        session,
        checklist_category_update,
        id=category_id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.delete("/system-checklist-categories/{category_id}")
async def delete_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """체크리스트 카테고리 삭제"""
    return await suggest_checklists_crud.delete(session, id=category_id)


@router.get("/checklist-categories", response_model=list[ChecklistCategory])
async def list_user_checklist_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 목록 조회"""
    return await suggest_checklists_crud.get_multi(
        session,
        user_id=current_user.id,
        schema_to_select=ChecklistCategory,
        return_as_model=True,
    )


@router.get("/checklist-categories/{category_id}", response_model=ChecklistCategory)
async def get_user_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 상세 조회"""
    return await suggest_checklists_crud.get(
        session,
        id=category_id,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.post("/checklist-categories", response_model=ChecklistCategory)
async def create_checklist_category(
    checklist_category_create: ChecklistCategoryCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 생성"""
    return await suggest_checklists_crud.create(
        session,
        InternalChecklistCategoryCreate(
            display_name=checklist_category_create.display_name,
            is_system_category=False,
            user_id=current_user.id,
        ),
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.put("/checklist-categories/{category_id}", response_model=ChecklistCategory)
async def update_user_checklist_category(
    category_id: int = Path(...),
    checklist_category_update: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 업데이트"""
    return await suggest_checklists_crud.update(
        session,
        checklist_category_update,
        id=category_id,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.delete("/checklist-categories/{category_id}")
async def delete_user_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 삭제"""
    return await suggest_checklists_crud.delete(
        session,
        id=category_id,
        user_id=current_user.id,
    )


@router.get("/suggest-items")
async def list_suggest_checklists(
    checklist_category_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    query = {}

    if checklist_category_id:
        query["checklist_category_id"] = checklist_category_id

    suggest_checklist = await suggest_checklists_crud.get_multi(
        session,
        offset=offset,
        limit=limit,
        **query,
    )

    return suggest_checklist.get("data")


@router.get("/suggest-items/{checklist_id}", response_model=SuggestChecklist)
async def get_suggest_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 제공 기본 체크리스트 항목 조회"""
    return await suggest_checklists_crud.get(
        session,
        id=checklist_id,
        return_as_model=True,
        schema_to_select=SuggestChecklist,
    )


@router.post("/suggest-items", response_model=SuggestChecklist)
async def create_suggest_checklist(
    suggest_checklist_create: SuggestChecklistCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 생성"""
    return await suggest_checklists_crud.create(
        session,
        suggest_checklist_create,
        return_as_model=True,
        schema_to_select=SuggestChecklist,
    )


@router.put("/suggest-items/{checklist_id}", response_model=SuggestChecklist)
async def update_suggest_checklist(
    checklist_id: int = Path(...),
    suggest_checklist_update: SuggestChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 업데이트"""
    return await suggest_checklists_crud.update(
        session,
        suggest_checklist_update,
        id=checklist_id,
        return_as_model=True,
        schema_to_select=SuggestChecklist,
    )


@router.delete("/suggest-items/{checklist_id}")
async def delete_suggest_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 삭제"""
    return await suggest_checklists_crud.delete(session, id=checklist_id)


@router.get("/user-checklist", response_model=list[UserChecklistResponse])
async def list_user_checklists(
    checklist_category_id: int | None = Query(None),
    completed_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 목록 조회 (카테고리별, 완료 상태별 필터링 가능)"""
    query = {"user_id": current_user.id, "is_deleted": False}

    # 카테고리 필터링
    if checklist_category_id is not None:
        query["checklist_category_id"] = checklist_category_id

    # 완료된 항목만 조회
    if completed_only:
        query["is_completed"] = True

    user_checklist = await user_checklists_crud.get_multi(
        session,
        schema_to_select=UserChecklist,
        return_as_model=True,
        **query,
    )

    return user_checklist.get("data")


@router.post("/user-checklists")
async def create_user_checklists(
    suggest_item_ids: list[int] = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    suggest_item_ids = list(set(suggest_item_ids))

    # 선택된 기본 체크리스트 항목들 조회
    suggest_items = await suggest_checklists_crud.get_multi(
        session,
        id__in=suggest_item_ids,
        schema_to_select=SuggestChecklist,
        return_as_model=True,
    )

    if not suggest_items.get("data"):
        raise HTTPException(status_code=404, detail="Selected items not found")

    # 선택한 항목들을 유저 체크리스트로 변환
    user_checklist_items = []
    for suggest_item in suggest_items.get("data"):
        user_checklist_item = UserChecklist(
            title=suggest_item.title,
            description=suggest_item.description,
            suggest_item_id=suggest_item.id,
            user_id=current_user.id,
            checklist_category_id=suggest_item.checklist_category_id,
        )
        user_checklist_items.append(user_checklist_item)

        await user_checklists_crud.create(
            session,
            user_checklist_item,
        )

    return user_checklist_items


@router.post("/custom-checklists", response_model=UserChecklistResponse)
async def create_custom_checklist(
    checklist: UserChecklistCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 정의 체크리스트 항목 생성 (추천에서 가져오지 않는 경우)"""
    new_checklist = UserChecklist(
        title=checklist.title,
        description=checklist.description,
        user_id=current_user.id,
        checklist_category_id=checklist.checklist_category_id,
    )

    result = await user_checklists_crud.create(session, new_checklist)
    return result


@router.put("/user-checklists/order", response_model=list[UserChecklistResponse])
async def update_checklists_order(
    order_data: list[ChecklistOrderUpdate] = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 순서 업데이트"""

    checklist_ids = [item.id for item in order_data]
    user_checklists = await user_checklists_crud.get_multi(
        session,
        id__in=checklist_ids,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=UserChecklist,
    )

    if len(user_checklists.get("data", [])) != len(checklist_ids):
        raise HTTPException(
            status_code=400,
            detail="하나 이상의 체크리스트 항목이 사용자의 것이 아닙니다",
        )

    # 각 체크리스트 항목의 순서 업데이트
    results = []
    for item in order_data:
        existing_item = await user_checklists_crud.get(
            session, id=item.id, return_as_model=True, schema_to_select=UserChecklist
        )
        updated_item = await user_checklists_crud.update(
            session,
            {"display_order": item.display_order},
            id=existing_item.id,
            return_as_model=True,
            schema_to_select=UserChecklist,
        )
        results.append(updated_item)

    return results


@router.put("/user-checklists/{checklist_id}", response_model=UserChecklistResponse)
async def update_user_checklist(
    checklist_id: int = Path(...),
    checklist_update: UserChecklistUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 업데이트 (완료/미완료 상태 포함)"""

    existing_checklist = await user_checklists_crud.get(
        session,
        id=checklist_id,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=UserChecklist,
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="해당 체크리스트를 찾을 수 없거나 사용자의 것이 아닙니다",
        )

    update_data = checklist_update.model_dump(exclude_none=True)

    if (
        "is_completed" in update_data
        and update_data["is_completed"] != existing_checklist.is_completed
    ):
        update_data["completed_datetime"] = (
            datetime.now() if update_data["is_completed"] else None
        )

    return await user_checklists_crud.update(
        session,
        update_data,
        id=existing_checklist.id,
        return_as_model=True,
        schema_to_select=UserChecklist,
    )


@router.delete("/user-checklists/{checklist_id}")
async def delete_user_checklist(
    checklist_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    existing_checklist = await user_checklists_crud.get(
        session,
        id=checklist_id,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=UserChecklist,
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="해당 체크리스트를 찾을 수 없거나 사용자의 것이 아닙니다",
        )

    await user_checklists_crud.delete(
        session,
        id=existing_checklist.id,
    )
