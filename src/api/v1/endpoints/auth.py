from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_oauth_client
from core import security
from core.config import settings
from core.db import get_session
from core.exceptions import InvalidAuthorizationCode, InvalidToken
from core.oauth_client import OAuthClient
from cruds.crud_users import user_crud
from models.auth import AuthToken, KakaoLoginData, NaverLoginData
from models.users import SocialProviderEnum, UserCreate

router = APIRouter()


@router.post("/naver-login")
async def naver_login(
    login_data: NaverLoginData,
    session: AsyncSession = Depends(get_session),
    oauth_client: OAuthClient = Depends(get_oauth_client),
):
    try:
        token_data = await oauth_client.get_tokens(login_data.code, login_data.state)
    except InvalidAuthorizationCode:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    try:
        oauth_result = await oauth_client.get_user_info(token_data["access_token"])
        user_info = oauth_result["response"]
        user_data = {
            "email": user_info["email"],
            "id": user_info["id"],
            "mobile": user_info.get("mobile", ""),
            "name": user_info.get("name"),
            "profile_image": user_info.get("profile_image"),
            "age": user_info.get("age"),
            "birthday": user_info.get("birthday"),
            "gender": user_info.get("gender"),
        }

    except InvalidToken:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await user_crud.get(session=session, email=user_data["email"])

    is_new_user = False
    if not user:
        user = await user_crud.create(
            session=session,
            user_create=UserCreate(
                email=user_data["email"],
                phone_number=user_data["mobile"],
                social_provider=SocialProviderEnum.naver,
            ),
        )
        is_new_user = True

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=is_new_user,
        user_nickname=user.nickname,
    )


@router.post("/kakao-login")
async def kakao_login(
    login_data: KakaoLoginData,
    session: AsyncSession = Depends(get_session),
    oauth_client: OAuthClient = Depends(get_oauth_client),
):
    try:
        token_data = await oauth_client.get_tokens(login_data.code, login_data.state)
    except InvalidAuthorizationCode:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    try:
        user_info = await oauth_client.get_user_info(token_data["access_token"])

        user_data = {
            "email": user_info["kakao_account"]["email"],
            "id": user_info["id"],
            "mobile": user_info.get("mobile", ""),
            "name": user_info.get("name"),
            "profile_image": user_info.get("profile_image"),
            "age": user_info.get("age"),
            "birthday": user_info.get("birthday"),
            "gender": user_info.get("gender"),
        }

    except InvalidToken:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await user_crud.get(session=session, email=user_data["email"])

    is_new_user = False
    if not user:
        user = await user_crud.create(
            session=session,
            user_create=UserCreate(
                email=user_data["email"],
                phone_number=user_data["mobile"],
                social_provider=SocialProviderEnum.kakao,
            ),
        )
        is_new_user = True

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=is_new_user,
        user_nickname=user.nickname,
    )


@router.post("/anonymous-login")
async def anonymous_login(
    session: AsyncSession = Depends(get_session),
):
    user = await user_crud.create(
        session,
        UserCreate(
            email="1233@example.com",
            phone_number="",
            social_provider=SocialProviderEnum.anonymous,
        ),
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=True,
        user_nickname=user.nickname,
    )
