from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from crud import checklist as crud_checklist
from crud import checklist_category as crud_category
from models import User
from schemes.checklists import (
    ChecklistRead,
    ChecklistCreate,
    ChecklistOrderUpdate,
    ChecklistUpdate,
    SuggestChecklistRead,
    ChecklistCreateBySystem,
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
    checklists = await crud_checklist.get_system_checklists(
        db=session, skip=skip, limit=limit
    )
    return [SuggestChecklistRead.model_validate(c) for c in checklists]


@router.get("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def get_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 제공 기본 체크리스트 항목 조회"""
    checklist = await crud_checklist.get(db=session, id=checklist_id)

    if not checklist or not checklist.is_system_checklist:
        raise HTTPException(status_code=404, detail="Suggest checklist not found")

    return SuggestChecklistRead.model_validate(checklist)


@router.post("/system", response_model=SuggestChecklistRead)
async def create_system_checklist(
    system_checklist_create: ChecklistCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 생성"""
    # 카테고리 검증
    category = await crud_category.get(
        db=session, id=system_checklist_create.checklist_category_id
    )

    if not category or not category.is_system_category:
        raise HTTPException(
            status_code=400,
            detail="System checklist category not found",
        )

    # system_checklist_create에 is_system_checklist 필드 추가
    checklist_data = system_checklist_create.model_dump()
    checklist_data["is_system_checklist"] = True

    checklist = await crud_checklist.create(db=session, obj_in=checklist_data)
    return SuggestChecklistRead.model_validate(checklist)


@router.put("/system/{checklist_id}", response_model=SuggestChecklistRead)
async def update_system_checklist(
    checklist_id: int = Path(...),
    system_checklist_update: ChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 업데이트"""
    # 체크리스트 조회
    checklist = await crud_checklist.get(db=session, id=checklist_id)

    if not checklist or not checklist.is_system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    # 카테고리 변경 시 검증
    if system_checklist_update.checklist_category_id:
        category = await crud_category.get(
            db=session, id=system_checklist_update.checklist_category_id
        )

        if not category or not category.is_system_category:
            raise HTTPException(
                status_code=400,
                detail="System checklist category not found",
            )

    # 업데이트
    updated_checklist = await crud_checklist.update(
        db=session, db_obj=checklist, obj_in=system_checklist_update
    )
    return SuggestChecklistRead.model_validate(updated_checklist)


@router.delete("/system/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_system_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 삭제"""
    checklist = await crud_checklist.get(db=session, id=checklist_id)

    if not checklist or not checklist.is_system_checklist:
        raise HTTPException(
            status_code=404,
            detail="Suggest checklist not found",
        )

    await crud_checklist.soft_delete(db=session, id=checklist_id)
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
    if category_id:
        checklists = await crud_checklist.get_by_category(
            db=session,
            category_id=category_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    else:
        checklists = await crud_checklist.get_by_user(
            db=session, user_id=current_user.id, skip=skip, limit=limit
        )

    return [ChecklistRead.model_validate(c) for c in checklists]


@router.post("/by-system", response_model=list[ChecklistRead])
async def create_checklists_by_system(
    checklist_create: ChecklistCreateBySystem,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 생성"""
    user_checklists = await crud_checklist.create_from_system_checklist(
        db=session,
        system_checklist_ids=checklist_create.system_checklist_ids,
        user_id=current_user.id,
    )

    if not user_checklists:
        raise HTTPException(status_code=404, detail="System checklist not found")

    return [
        ChecklistRead.model_validate(user_checklist)
        for user_checklist in user_checklists
    ]


@router.post("", response_model=ChecklistRead)
async def create_checklist(
    checklist: ChecklistCreate = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 정의 체크리스트 항목 생성 (추천에서 가져오지 않는 경우)"""
    # 카테고리 검증
    category = await crud_category.get(db=session, id=checklist.checklist_category_id)

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Checklist category not found",
        )

    if not category.is_system_category and category.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create checklist in this category",
        )

    # 마지막 표시 순서 가져오기
    global_order = await crud_checklist.get_last_global_order(
        db=session, user_id=current_user.id
    )

    category_order = await crud_checklist.get_last_category_order(
        db=session, user_id=current_user.id, category_id=checklist.checklist_category_id
    )

    # 데이터 준비
    checklist_data = checklist.model_dump()
    checklist_data.update(
        {
            "user_id": current_user.id,
            "is_system_checklist": False,
            "global_display_order": global_order + 1,
            "category_display_order": category_order + 1,
        }
    )

    # 체크리스트 생성
    new_checklist = await crud_checklist.create(db=session, obj_in=checklist_data)

    return ChecklistRead.model_validate(new_checklist)


@router.put("/reorder", response_model=list[ChecklistRead])
async def update_checklists_order(
    checklist_order_data: list[ChecklistOrderUpdate] = Body(...),
    is_global_order: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자 체크리스트 항목 순서 업데이트"""
    results = []

    for item in checklist_order_data:
        checklist = await crud_checklist.get(db=session, id=item.id)

        if not checklist or checklist.user_id != current_user.id:
            # 존재하지 않는 체크리스트나 다른 사용자의 체크리스트는 건너뛰기
            continue

        if is_global_order:
            updated_checklist = await crud_checklist.update_display_order(
                db=session, checklist_id=item.id, global_order=item.display_order
            )
        else:
            updated_checklist = await crud_checklist.update_display_order(
                db=session, checklist_id=item.id, category_order=item.display_order
            )

        results.append(updated_checklist)

    return [ChecklistRead.model_validate(c) for c in results]


@router.put("/{checklist_id}", response_model=ChecklistRead)
async def update_checklist(
    checklist_id: int = Path(...),
    checklist_update: ChecklistUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 수정"""
    checklist = await crud_checklist.get(db=session, id=checklist_id)

    if not checklist or checklist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Checklist not found")

    updated_checklist = await crud_checklist.update(
        db=session, db_obj=checklist, obj_in=checklist_update
    )

    return ChecklistRead.model_validate(updated_checklist)


@router.delete("/{checklist_id}", response_model=ResponseWithStatusMessage)
async def delete_checklist(
    checklist_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 삭제"""
    checklist = await crud_checklist.get(db=session, id=checklist_id)

    if not checklist or checklist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Checklist not found")

    await crud_checklist.soft_delete(db=session, id=checklist_id)

    return ResponseWithStatusMessage(message="Checklist deleted successfully")
