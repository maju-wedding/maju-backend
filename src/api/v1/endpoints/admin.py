from uuid import UUID

from fastapi import Body, Depends, Path, HTTPException, Query, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_admin
from core.db import get_session
from crud import (
    category as crud_category,
    checklist as crud_checklist,
    suggest_search_keyword as crud_keyword,
    user as crud_user,
)
from models import User
from schemes.checklists import (
    CategoryRead,
    CategoryCreateBySystem,
    CategoryUpdate,
    SuggestChecklistRead,
    ChecklistCreate,
    ChecklistUpdate,
)
from schemes.common import ResponseWithStatusMessage
from schemes.suggest_search_keywords import SuggestSearchKeywordRead

router = APIRouter()


@router.post("/categories/system", response_model=CategoryRead)
async def create_system_category(
    category_create: CategoryCreateBySystem = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 생성"""
    category = await crud_category.create_system_category(
        db=session, display_name=category_create.display_name
    )

    return CategoryRead(
        id=category.id,
        display_name=category.display_name,
        user_id=category.user_id,
        is_system_category=category.is_system_category,
        checklists_count=0,
    )


@router.put("/categories/system/{category_id}", response_model=CategoryRead)
async def update_system_category(
    category_id: int = Path(...),
    category_update: CategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 업데이트"""
    category = await crud_category.get(db=session, id=category_id)

    if not category or not category.is_system_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    updated_category = await crud_category.update(
        db=session, db_obj=category, obj_in=category_update
    )

    return CategoryRead(
        id=updated_category.id,
        display_name=updated_category.display_name,
        user_id=updated_category.user_id,
        is_system_category=updated_category.is_system_category,
        checklists_count=0,  # 여기서는 개수를 다시 조회하지 않음
    )


@router.delete(
    "/categories/system/{category_id}",
    response_model=ResponseWithStatusMessage,
)
async def delete_system_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 체크리스트 카테고리 삭제"""
    category = await crud_category.get(db=session, id=category_id)

    if not category or not category.is_system_category:
        raise HTTPException(status_code=404, detail="Checklist category not found")

    await crud_category.soft_delete_with_checklists(db=session, category_id=category_id)

    return ResponseWithStatusMessage(message="Checklist category deleted")


@router.post("/checklists/system", response_model=SuggestChecklistRead)
async def create_system_checklist(
    system_checklist_create: ChecklistCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """시스템 제공 기본 체크리스트 항목 생성"""
    # 카테고리 검증
    category = await crud_category.get(
        db=session, id=system_checklist_create.category_id
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


@router.put("/checklists/system/{checklist_id}", response_model=SuggestChecklistRead)
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
    if system_checklist_update.category_id:
        category = await crud_category.get(
            db=session, id=system_checklist_update.category_id
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


@router.delete(
    "/checklists/system/{checklist_id}", response_model=ResponseWithStatusMessage
)
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


@router.post("/suggest-search-keywords", response_model=SuggestSearchKeywordRead)
async def create_suggest_search_keyword(
    keyword: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """검색어 추천 생성"""
    # 이미 존재하는지 확인
    existing_keyword = await crud_keyword.get_by_keyword(db=session, keyword=keyword)

    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # 키워드 생성
    new_keyword = await crud_keyword.create(db=session, obj_in={"keyword": keyword})

    return SuggestSearchKeywordRead(id=new_keyword.id, keyword=new_keyword.keyword)


@router.put(
    "/suggest-search-keywords/{keyword_id}", response_model=SuggestSearchKeywordRead
)
async def update_suggest_search_keyword(
    keyword_id: int,
    keyword: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """검색어 추천 수정"""
    existing_keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not existing_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # 중복 확인
    duplicate = await crud_keyword.get_by_keyword(db=session, keyword=keyword)

    if duplicate and duplicate.id != keyword_id:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # 업데이트
    updated_keyword = await crud_keyword.update(
        db=session, db_obj=existing_keyword, obj_in={"keyword": keyword}
    )

    return SuggestSearchKeywordRead(
        id=updated_keyword.id, keyword=updated_keyword.keyword
    )


@router.delete("/suggest-search-keywords/{keyword_id}")
async def delete_suggest_search_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """검색어 추천 삭제"""
    keyword = await crud_keyword.get(db=session, id=keyword_id)

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await crud_keyword.soft_delete(db=session, id=keyword_id)

    return {"message": "Keyword deleted successfully"}


@router.get("/users", status_code=status.HTTP_200_OK, response_model=list[User])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """관리자용 사용자 목록 조회"""
    users = await crud_user.get_multi(db=session, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """사용자 상세 정보 조회"""
    user = await crud_user.get(db=session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
