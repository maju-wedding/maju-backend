from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
from core.db import get_session

from cruds.checklists import user_checklists_crud, suggest_checklists_crud
from models import User
from models.checklist import UserChecklist, SuggestChecklist

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


@router.get("/user-checklist")
async def list_user_checklists(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user_checklist = await user_checklists_crud.get_multi(
        session,
        user_id=current_user.id,
        schema_to_select=UserChecklist,
        return_as_model=True,
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
