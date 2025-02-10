from fastapi import APIRouter, Body, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from cruds.crud_users import user_crud
from models.users import UserUpdate, User, UserRead

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """
    내 정보 조회
    """
    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(current_user),
    }


@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_user_me(
    user_update: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    내 정보 업데이트
    """
    updated_user = await user_crud.update(
        session, user_update.model_dump(exclude_unset=True), id=current_user.id
    )

    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(updated_user),
    }


@router.get("/", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """관리자용 사용자 목록 조회"""
    users = await user_crud.get_multi(
        session,
        offset=offset,
        limit=limit,
        is_active=True,
        is_deleted=False,
    )

    return users.get("data", [])


@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """사용자 삭제 (soft delete)"""
    user = await user_crud.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot delete superuser")

    await user_crud.update(session, {"is_deleted": True}, id=user_id)

    return {"success": True, "message": "", "data": None}
