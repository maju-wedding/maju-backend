from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_oauth_client
from core import security
from core.config import settings
from core.db import get_session
from core.enums import UserTypeEnum
from core.exceptions import InvalidToken
from core.oauth_client import extract_user_data
from cruds.users import users_crud
from models.users import SocialProviderEnum, User
from schemes.auth import AuthToken, SocialLoginWithTokenData
from schemes.users import (
    UserCreate,
    InternalUserCreate,
)
from utils.utils import generate_guest_nickname

router = APIRouter()


@router.post("/register", response_model=AuthToken)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    일반 사용자 회원가입

    - 이메일과 비밀번호로 새로운 계정을 생성합니다.
    - 회원가입 성공시 자동으로 로그인되어 토큰이 반환됩니다.
    """
    # 이메일 중복 체크
    existing_user = await users_crud.get(session, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_phone_number = await users_crud.get(
        session, phone_number=user_data.phone_number
    )
    if existing_phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    # 비밀번호 해싱
    hashed_password = security.get_password_hash(user_data.password.get_secret_value())

    # 사용자 생성
    user = await users_crud.create(
        session,
        InternalUserCreate(
            email=user_data.email,
            phone_number=user_data.phone_number,
            nickname=user_data.nickname,
            hashed_password=hashed_password,
            user_type=UserTypeEnum.local,
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
        nickname=user.nickname,
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
    user = await users_crud.get(
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
        nickname=user.nickname,
    )


@router.post("/social-login")
async def social_login(
    login_data: SocialLoginWithTokenData,
    session: AsyncSession = Depends(get_session),
):
    oauth_client = get_oauth_client(login_data.provider)

    """소셜 로그인 (카카오, 네이버) - SDK에서 받은 액세스 토큰 사용"""
    if login_data.provider not in [SocialProviderEnum.kakao, SocialProviderEnum.naver]:
        raise ValueError(f"Unsupported provider: {login_data.provider}")

    try:
        # 액세스 토큰 유효성 검증
        is_valid = await oauth_client.is_authenticated(login_data.access_token)
        if not is_valid:
            raise InvalidToken

        # 액세스 토큰으로 사용자 정보 가져오기
        raw_user_info = await oauth_client.get_user_info(login_data.access_token)
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Invalid access token")

    user_data = extract_user_data(login_data.provider, raw_user_info)

    # 기존 사용자 확인 또는 신규 사용자 생성
    user = await users_crud.get(
        session,
        email=user_data["email"],
        is_deleted=False,
        return_as_model=True,
        schema_to_select=User,
    )

    if not user:
        user = await users_crud.create(
            session,
            InternalUserCreate(
                email=user_data["email"],
                phone_number=user_data["mobile"],
                social_provider=login_data.provider,
                nickname=user_data["name"],
                user_type=UserTypeEnum.social,
                gender=user_data["gender"],
            ),
        )

    # JWT 토큰 생성 및 반환
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jwt_token = security.create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
        user_type=UserTypeEnum.social,
        extra_claims={"provider": user.social_provider},
    )

    return AuthToken(
        access_token=jwt_token,
        token_type="bearer",
        nickname=user.nickname,
    )


@router.post("/guest-login")
async def guest_login(
    session: AsyncSession = Depends(get_session),
):
    """게스트 로그인 (비회원)"""
    user = await users_crud.create(
        session,
        InternalUserCreate(
            nickname=generate_guest_nickname(),
            user_type=UserTypeEnum.guest,
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
        nickname=user.nickname,
    )
