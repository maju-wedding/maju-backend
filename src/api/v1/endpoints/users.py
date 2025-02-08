from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user
from core.db import get_session
from cruds.crud_users import user_crud
from models.users import UserUpdate, User

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
