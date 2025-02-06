from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
from starlette import status

from api.v1.deps import CurrentUser, SessionDep
from cruds import users as users_crud
from models.users import UserPublic, UserUpdateMe

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserPublic)
async def read_user_me(current_user: CurrentUser):
    """
    내 정보 조회
    """
    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(current_user),
    }


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserPublic)
async def update_user_me(
    session: SessionDep,
    current_user: CurrentUser,
    user_update: UserUpdateMe = Body(...),
):
    """
    내 정보 업데이트
    """
    updated_user = await users_crud.update_user(
        session=session, user=current_user, user_update=user_update
    )

    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(updated_user),
    }
