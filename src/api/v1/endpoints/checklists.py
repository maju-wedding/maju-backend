from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
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
    # 1. 시스템 체크리스트 목록 조회
    system_checklists = await crud_checklist.get_system_checklists_by_ids(
        db=session, ids=checklist_create.system_checklist_ids
    )

    if not system_checklists:
        raise HTTPException(status_code=404, detail="System checklist not found")

    # 2. 시스템 체크리스트의 카테고리 정보 수집
    category_ids = {
        checklist.checklist_category_id
        for checklist in system_checklists
        if checklist.checklist_category_id
    }

    # 3. 사용자의 카테고리 조회 (기존에 있는지 확인)
    user_categories = await crud_category.get_user_categories(
        db=session, user_id=current_user.id
    )
    user_category_map = {}

    # 4. 사용자의 카테고리 중에서 시스템 카테고리에 대응되는 것이 있는지 확인
    for system_category_id in category_ids:
        # 시스템 카테고리 정보 조회
        system_category = await crud_category.get(db=session, id=system_category_id)
        if not system_category:
            continue

        # 같은 이름의 사용자 카테고리가 있는지 확인
        matching_categories = [
            category
            for category in user_categories
            if category.display_name == system_category.display_name
        ]

        if matching_categories:
            # 이미 존재하는 카테고리 사용
            user_category_map[system_category_id] = matching_categories[0].id
        else:
            # 새 카테고리 생성
            new_category = await crud_category.create_user_category(
                db=session,
                display_name=system_category.display_name,
                user_id=current_user.id,
            )
            user_category_map[system_category_id] = new_category.id

    # 5. 체크리스트 생성 (기존 카테고리 ID를 사용자 카테고리 ID로 매핑)
    user_checklists = (
        await crud_checklist.create_from_system_checklist_with_category_mapping(
            db=session,
            system_checklist_ids=checklist_create.system_checklist_ids,
            user_id=current_user.id,
            category_mapping=user_category_map,
        )
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
    # 입력된 카테고리 ID 확인
    input_category_id = checklist.checklist_category_id

    # 카테고리 검증 및 처리
    system_category = None
    user_category = None

    # 먼저 카테고리가 존재하는지 확인
    category = await crud_category.get(db=session, id=input_category_id)
    if not category:
        raise HTTPException(
            status_code=400,
            detail="Checklist category not found",
        )

    # 카테고리 유형 확인 및 처리
    if category.is_system_category:
        # 시스템 카테고리인 경우, 사용자가 이미 동일한 이름의 카테고리를 가지고 있는지 확인
        system_category = category
        user_categories = await crud_category.get_user_categories(
            db=session, user_id=current_user.id
        )

        # 사용자의 카테고리 중 동일한 이름을 가진 카테고리 찾기
        matching_categories = [
            cat
            for cat in user_categories
            if cat.display_name == system_category.display_name
        ]

        if matching_categories:
            # 이미 동일한 이름의 카테고리가 있으면 그것을 사용
            user_category = matching_categories[0]
        else:
            # 없으면 새로 생성
            user_category = await crud_category.create_user_category(
                db=session,
                display_name=system_category.display_name,
                user_id=current_user.id,
            )

        # 사용자 체크리스트에 연결할 카테고리 ID 업데이트
        actual_category_id = user_category.id
    else:
        # 이미 사용자 카테고리인 경우, 해당 카테고리가 현재 사용자의 것인지 확인
        if category.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to create checklist in this category",
            )

        # 사용자 카테고리 그대로 사용
        user_category = category
        actual_category_id = user_category.id

    # 마지막 표시 순서 가져오기
    global_order = await crud_checklist.get_last_global_order(
        db=session, user_id=current_user.id
    )

    category_order = await crud_checklist.get_last_category_order(
        db=session, user_id=current_user.id, category_id=actual_category_id
    )

    # 데이터 준비
    checklist_data = checklist.model_dump()
    # 카테고리 ID 업데이트
    checklist_data["checklist_category_id"] = actual_category_id
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


@router.post("/clear", response_model=ResponseWithStatusMessage)
async def clear_user_checklist(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """사용자의 모든 체크리스트를 삭제 처리"""
    # 사용자의 모든 체크리스트를 소프트 삭제
    deleted_count = await crud_checklist.soft_delete_all_by_user(
        db=session, user_id=current_user.id
    )

    return ResponseWithStatusMessage(
        status="success",
        message=f"{deleted_count}개의 체크리스트가 삭제되었습니다.",
        data={"deleted_count": deleted_count},
    )


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

    return ResponseWithStatusMessage(
        status="success", message="Checklist deleted successfully"
    )
