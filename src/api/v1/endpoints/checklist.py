from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
from core.db import get_session
from cruds.crud_checklist import default_checklist_item_crud, user_checklist_crud
from models import User
from models.checklist import DefaultChecklistItem, UserChecklist

router = APIRouter()


@router.get("/default-items")
async def list_default_items(
    category_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    query = {}

    if category_id:
        query["category_id"] = category_id

    default_checklist = await default_checklist_item_crud.get(
        session,
        query,
        schema_to_select=DefaultChecklistItem,
        return_as_model=True,
    )

    return default_checklist.get("data")


@router.get("/user-checklist")
async def list_user_checklists(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user_checklist = await user_checklist_crud.get(
        session,
        user_id=current_user.id,
        schema_to_select=UserChecklist,
        return_as_model=True,
    )

    return user_checklist.get("data")


@router.post("/user-checklist/{checklist_id}/items")
async def add_checklist_item(
    checklist_id: int = Path(...),
    default_item_id: int = Body(...),
):
    return {"message": "Hello World"}


@router.patch("/{checklist_id}")
async def update_checklist(checklist_id: int):
    return {"message": "Hello World"}


@router.delete("/{checklist_id}")
async def delete_checklist(checklist_id: int):
    return {"message": "Hello World"}
