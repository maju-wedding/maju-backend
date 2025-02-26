from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
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
)

router = APIRouter()


@router.get("/suggest-items")
async def list_suggest_checklists(
    category_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    query = {}

    if category_id:
        query["category_id"] = category_id

    suggest_checklist = await suggest_checklists_crud.get_multi(
        session,
        offset=offset,
        limit=limit,
        **query,
    )

    return suggest_checklist.get("data")


@router.get("/user-checklist", response_model=list[UserChecklistResponse])
async def list_user_checklists(
    category_id: int | None = Query(None),
    completed_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 목록 조회 (카테고리별, 완료 상태별 필터링 가능)"""
    query = {"user_id": current_user.id, "is_deleted": False}

    # 카테고리 필터링
    if category_id is not None:
        query["category_id"] = category_id

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
            category_id=suggest_item.category_id,
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
        category_id=checklist.category_id,
        suggest_item_id=0,  # 사용자 정의 항목은 0 또는 null로 표시
    )

    result = await user_checklists_crud.create(session, new_checklist)
    return result


@router.put("/user-checklists/{checklist_id}", response_model=UserChecklistResponse)
async def update_user_checklist(
    checklist_id: int = Path(...),
    checklist_update: UserChecklistUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 업데이트 (완료/미완료 상태 포함)"""
    # 체크리스트가 사용자의 것인지 확인
    existing_checklist = await user_checklists_crud.get(
        session, id=checklist_id, user_id=current_user.id
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="해당 체크리스트를 찾을 수 없거나 사용자의 것이 아닙니다",
        )

    update_data = {k: v for k, v in checklist_update.dict().items() if v is not None}

    # 완료 상태 변경 시 completed_at 업데이트
    if (
        "is_completed" in update_data
        and update_data["is_completed"] != existing_checklist["is_completed"]
    ):
        update_data["completed_at"] = (
            datetime.now() if update_data["is_completed"] else None
        )

    return await user_checklists_crud.update(session, existing_checklist, update_data)


@router.delete("/user-checklists/{checklist_id}", response_model=UserChecklistResponse)
async def delete_user_checklist(
    checklist_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 삭제 (소프트 삭제)"""
    existing_checklist = await user_checklists_crud.get(
        session, id=checklist_id, user_id=current_user.id
    )

    if not existing_checklist:
        raise HTTPException(
            status_code=404,
            detail="해당 체크리스트를 찾을 수 없거나 사용자의 것이 아닙니다",
        )

    # 소프트 삭제
    return await user_checklists_crud.update(
        session, existing_checklist, {"is_deleted": True}
    )


@router.put("/user-checklists/order", response_model=list[UserChecklistResponse])
async def update_checklists_order(
    order_data: list[ChecklistOrderUpdate] = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 순서 업데이트"""
    # 모든 체크리스트 ID가 사용자의 것인지 확인
    checklist_ids = [item.id for item in order_data]
    user_checklists = await user_checklists_crud.get_multi(
        session, id__in=checklist_ids, user_id=current_user.id
    )

    if len(user_checklists.get("data", [])) != len(checklist_ids):
        raise HTTPException(
            status_code=400,
            detail="하나 이상의 체크리스트 항목이 사용자의 것이 아닙니다",
        )

    # 각 체크리스트 항목의 순서 업데이트
    results = []
    for item in order_data:
        existing_item = await user_checklists_crud.get(session, id=item.id)
        updated_item = await user_checklists_crud.update(
            session, existing_item, {"order": item.order}
        )
        results.append(updated_item)

    return results
