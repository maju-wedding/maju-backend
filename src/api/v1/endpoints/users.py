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
        session, user_update.dict(exclude_unset=True), id=current_user.id
    )

    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(updated_user),
    }


@router.get("/", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    email: str | None = None,
    is_active: bool | None = None,
    is_deleted: bool | None = None,
    current_user: User = Depends(get_current_admin),
):
    """관리자용 사용자 목록 조회"""
    return await user_crud.get_multi(
        db=session,
        email=email,
        is_active=is_active,
        is_deleted=is_deleted,
    )


@router.put("/users/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """사용자 활성화/비활성화"""
    user = await user_crud.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await user_crud.update(
        session, {"is_active": not user.is_active}, id=user_id
    )


@router.delete("/users/{user_id}", response_model=UserRead)
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

    return await user_crud.update(session, {"is_deleted": True}, id=user_id)


@router.post("/superuser", response_model=UserRead)
async def create_superuser(
    email: str = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """새로운 관리자 생성"""
    existing_user = await user_crud.get(session, email=email)
    if existing_user:
        if existing_user.is_superuser:
            raise HTTPException(status_code=400, detail="User is already a superuser")
        return await user_crud.update(
            session, db_obj=existing_user, obj_in={"is_superuser": True}
        )

    raise HTTPException(status_code=404, detail="User not found")
