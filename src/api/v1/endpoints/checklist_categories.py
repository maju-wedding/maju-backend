from fastapi import Depends, Path, HTTPException, Body, APIRouter
from fastcrud import JoinConfig
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_admin, get_current_user
from core.db import get_session
from cruds.checklists import checklist_categories_crud
from models import User, Checklist
from models.checklist_categories import ChecklistCategory
from schemes.checklists import (
    ChecklistCategoryRead,
    ChecklistCategoryCreateBySystem,
    InternalChecklistCategoryCreate,
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
    results = await checklist_categories_crud.get_multi_joined(
        session,
        is_system_category=True,
        is_deleted=False,
        joins_config=[
            JoinConfig(
                model=Checklist,
                join_on=Checklist.checklist_category_id == ChecklistCategory.id,
                join_prefix="checklists_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
        nest_joins=True,
        sort_columns=["id"],
    )

    return results.get("data", [])


@router.get(
    "/system",
    response_model=list[ChecklistCategoryRead],
)
async def list_system_checklist_categories(
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 목록 조회"""
    results = await checklist_categories_crud.get_multi_joined(
        session,
        is_system_category=True,
        is_deleted=False,
        joins_config=[
            JoinConfig(
                model=Checklist,
                join_on=Checklist.checklist_category_id == ChecklistCategory.id,
                join_prefix="checklists_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
        nest_joins=True,
        sort_columns=["id"],
    )

    if not results:
        raise HTTPException(status_code=404, detail="Checklist categories not found")

    checklist_categories = results.get("data", [])

    for category in checklist_categories:
        category["checklists_count"] = len(category["checklists"])

    return checklist_categories


@router.get("/system/{category_id}", response_model=ChecklistCategoryRead)
async def get_system_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """시스템 체크리스트 카테고리 상세 조회"""
    checklist_category = await checklist_categories_crud.get_joined(
        session,
        id=category_id,
        is_deleted=False,
        joins_config=[
            JoinConfig(
                model=Checklist,
                join_on=Checklist.checklist_category_id == ChecklistCategory.id,
                join_prefix="checklists_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
        nest_joins=True,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    return ChecklistCategoryRead(
        **checklist_category,
        checklists_count=len(checklist_category["checklists"]),
    )


@router.post("/system", response_model=ChecklistCategory)
async def create_system_checklist_category(
    checklist_category_create: ChecklistCategoryCreateBySystem = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 생성"""
    return await checklist_categories_crud.create(
        session,
        InternalChecklistCategoryCreate(
            display_name=checklist_category_create.display_name,
            is_system_category=True,
        ),
    )


@router.put("/system/{category_id}", response_model=ChecklistCategory)
async def update_system_checklist_category(
    category_id: int = Path(...),
    checklist_category_update: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 업데이트"""
    checklist_category = await checklist_categories_crud.get(
        session,
        id=category_id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    if not checklist_category.is_system_category:
        raise HTTPException(
            status_code=400, detail="Only system categories can be updated"
        )

    return await checklist_categories_crud.update(
        session,
        checklist_category_update,
        id=category_id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


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
    checklist_category = await checklist_categories_crud.get(
        session,
        id=category_id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    if not checklist_category.is_system_category:
        raise HTTPException(
            status_code=400, detail="Only system categories can be deleted"
        )

    await checklist_categories_crud.delete(session, id=category_id)

    return ResponseWithStatusMessage(
        status="success", message="Checklist category deleted"
    )


@router.get("", response_model=list[ChecklistCategoryRead])
async def list_checklist_categories(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 목록 조회"""
    user_categories = await checklist_categories_crud.get_multi(
        session,
        user_id=current_user.id,
        is_deleted=False,
        schema_to_select=ChecklistCategory,
        return_as_model=True,
    )

    user_categories = user_categories.get("data", [])

    return user_categories


@router.get("/{category_id}", response_model=ChecklistCategoryRead)
async def get_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 상세 조회"""
    checklist_category = await checklist_categories_crud.get(
        session,
        id=category_id,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    return {
        **checklist_category.dict(),
        "checklist_count": len(checklist_category.checklists),
    }


@router.post("", response_model=ChecklistCategoryRead)
async def create_checklist_category(
    checklist_category_create: ChecklistCategoryCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """체크리스트 카테고리 생성"""
    return await checklist_categories_crud.create(
        session,
        InternalChecklistCategoryCreate(
            display_name=checklist_category_create.display_name,
            is_system_category=False,
            user_id=current_user.id,
        ),
    )


@router.put("/{category_id}", response_model=ChecklistCategoryRead)
async def update_checklist_category(
    category_id: int = Path(...),
    checklist_category_update: ChecklistCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 업데이트"""
    checklist_category = await checklist_categories_crud.get(
        session,
        id=category_id,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    return await checklist_categories_crud.update(
        session,
        checklist_category_update,
        id=category_id,
        user_id=current_user.id,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )


@router.delete("/{category_id}", response_model=ResponseWithStatusMessage)
async def delete_checklist_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """사용자 체크리스트 카테고리 삭제"""
    checklist_category = await checklist_categories_crud.get(
        session,
        id=category_id,
        user_id=current_user.id,
        is_deleted=False,
        return_as_model=True,
        schema_to_select=ChecklistCategory,
    )

    if not checklist_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    await checklist_categories_crud.delete(
        session,
        id=category_id,
        user_id=current_user.id,
    )

    return ResponseWithStatusMessage(
        status="success", message="Checklist category deleted"
    )
