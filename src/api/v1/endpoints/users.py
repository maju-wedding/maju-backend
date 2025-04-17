from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user
from core.db import get_session
from crud import user as crud_user
from models import User
from schemes.common import ResponseWithStatusMessage
from schemes.users import UserUpdate, UserRead

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserRead)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """내 정보 조회"""
    return current_user


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 정보 업데이트"""
    updated_user = await crud_user.update(
        db=session, db_obj=current_user, obj_in=user_update
    )
    return updated_user


@router.delete(
    "/me", status_code=status.HTTP_200_OK, response_model=ResponseWithStatusMessage
)
async def delete_user_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 계정 삭제"""
    await crud_user.soft_delete(db=session, id=current_user.id)
    return ResponseWithStatusMessage(
        status="success",
        message="User deleted successfully",
    )
