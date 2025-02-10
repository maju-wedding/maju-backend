from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_oauth_client
from core import security
from core.config import settings
from core.db import get_session
from core.enums import UserTypeEnum
from core.exceptions import InvalidAuthorizationCode, InvalidToken
from core.oauth_client import OAuthClient
from cruds.crud_users import user_crud
from models.auth import AuthToken, SocialLoginData
from models.users import (
    SocialProviderEnum,
    UserCreateSocial,
    UserCreateGuest,
    UserCreateLocal,
    User,
)

router = APIRouter()


@router.post("/register", response_model=AuthToken)
async def register(
    user_data: UserCreateLocal,
    session: AsyncSession = Depends(get_session),
):
    """
    일반 사용자 회원가입

    - 이메일과 비밀번호로 새로운 계정을 생성합니다.
    - 회원가입 성공시 자동으로 로그인되어 토큰이 반환됩니다.
    """
    # 이메일 중복 체크
    existing_user = await user_crud.get(session, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 비밀번호 해싱
    hashed_password = security.get_password_hash(user_data.password.get_secret_value())

    # 사용자 생성
    user = await user_crud.create(
        session,
        User(
            hashed_password=hashed_password,
            **user_data.model_dump(exclude={"password"}),
        ),
    )

    # 로그인 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
        user_type=UserTypeEnum.local,
        extra_claims={"nickname": user.nickname},
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=True,
        user_nickname=user.nickname,
    )


@router.post("/login", response_model=AuthToken)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    """
    일반 사용자 로그인

    Form fields:
    - **username**: 사용자 이메일
    - **password**: 사용자 비밀번호
    """
    user = await user_crud.get(
        session, email=form_data.username, schema_to_select=User, return_as_model=True
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login with social provider",
        )

    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
        user_type=UserTypeEnum.local,
        extra_claims={"nickname": user.nickname},
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=False,
        user_nickname=user.nickname,
    )


def extract_user_data(
    provider: SocialProviderEnum, raw_user_info: dict[str, Any]
) -> dict[str, Any]:
    """Extract standardized user data from provider-specific response"""
    if provider == SocialProviderEnum.kakao:
        return {
            "email": raw_user_info["kakao_account"]["email"],
            "id": raw_user_info["id"],
            "mobile": raw_user_info.get("mobile", ""),
            "name": raw_user_info.get("name"),
            "profile_image": raw_user_info.get("profile_image"),
            "age": raw_user_info.get("age"),
            "birthday": raw_user_info.get("birthday"),
            "gender": raw_user_info.get("gender"),
        }
    elif provider == SocialProviderEnum.naver:
        user_info = raw_user_info["response"]
        return {
            "email": user_info["email"],
            "id": user_info["id"],
            "mobile": user_info.get("mobile", ""),
            "name": user_info.get("name"),
            "profile_image": user_info.get("profile_image"),
            "age": user_info.get("age"),
            "birthday": user_info.get("birthday"),
            "gender": user_info.get("gender"),
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")


@router.post("/social-login")
async def social_login(
    login_data: SocialLoginData,
    session: AsyncSession = Depends(get_session),
    oauth_client: OAuthClient = Depends(get_oauth_client),
):
    """Unified social login endpoint supporting multiple providers"""
    try:
        token_data = await oauth_client.get_tokens(login_data.code, login_data.state)
    except InvalidAuthorizationCode:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    if login_data.provider not in [SocialProviderEnum.kakao, SocialProviderEnum.naver]:
        raise ValueError(f"Unsupported provider: {login_data.provider}")

    try:
        raw_user_info = await oauth_client.get_user_info(token_data["access_token"])
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Invalid token")

    if login_data.provider == SocialProviderEnum.kakao:
        user_data = {
            "email": raw_user_info["kakao_account"]["email"],
            "id": raw_user_info["id"],
            "mobile": raw_user_info.get("mobile", ""),
            "name": raw_user_info.get("name"),
            "profile_image": raw_user_info.get("profile_image"),
            "age": raw_user_info.get("age"),
            "birthday": raw_user_info.get("birthday"),
            "gender": raw_user_info.get("gender"),
        }
    else:
        user_info = raw_user_info["response"]
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

    user = await user_crud.get(session, email=user_data["email"])

    is_new_user = False
    if not user:
        user = await user_crud.create(
            session,
            UserCreateSocial(
                email=user_data["email"],
                phone_number=user_data["mobile"],
                social_provider=login_data.provider,
            ),
        )
        is_new_user = True

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
        user_type=UserTypeEnum.social,
        extra_claims={"provider": user.social_provider.value},
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=is_new_user,
        user_nickname=user.nickname,
    )


@router.post("/guest-login")
async def guest_login(
    session: AsyncSession = Depends(get_session),
):
    user = await user_crud.create(
        session,
        UserCreateGuest(
            nickname="guest",
        ),
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        user_type=UserTypeEnum.guest,
        extra_claims={"nickname": user.nickname},
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        is_new_user=True,
        user_nickname=user.nickname,
    )
