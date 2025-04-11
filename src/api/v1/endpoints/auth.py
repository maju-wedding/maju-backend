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
from crud import user as crud_user
from models.users import SocialProviderEnum
from schemes.auth import AuthToken, SocialLoginWithTokenData, SocialUserCheckResponse
from schemes.users import UserCreate
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
    existing_user = await crud_user.get_by_email(db=session, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 전화번호 중복 체크
    existing_phone_user = await crud_user.get_by_phone_number(
        db=session, phone_number=user_data.phone_number
    )
    if existing_phone_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    # 사용자 생성
    user = await crud_user.create(db=session, obj_in=user_data)

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
    user = await crud_user.authenticate(
        db=session, email=form_data.username, password=form_data.password
    )

    if not user:
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


@router.post("/social/user-check", response_model=SocialUserCheckResponse)
async def social_user_check(
    login_data: SocialLoginWithTokenData,
    session: AsyncSession = Depends(get_session),
):
    """
    소셜 로그인 사용자 확인

    - 소셜 액세스 토큰으로 사용자 정보를 확인하고 계정 존재 여부를 반환합니다.
    - 존재하는 사용자인 경우 exists=True 반환
    - 신규 사용자인 경우 exists=False 반환하고 클라이언트는 약관동의 페이지로 이동해야 함
    """
    oauth_client = get_oauth_client(login_data.provider)

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

    # 사용자 정보 추출
    user_data = extract_user_data(login_data.provider, raw_user_info)

    # 기존 사용자 확인
    user = await crud_user.get_by_email(db=session, email=user_data["email"])

    return SocialUserCheckResponse(
        exists=user is not None,
    )


@router.post("/social/login", response_model=AuthToken)
async def social_login(
    login_data: SocialLoginWithTokenData,
    session: AsyncSession = Depends(get_session),
):
    """
    소셜 로그인 (기존 사용자)

    - 이미 가입된 소셜 계정으로 로그인합니다.
    - 계정이 없는 경우 404 에러가 발생합니다.
    """
    oauth_client = get_oauth_client(login_data.provider)

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

    # 기존 사용자 확인
    user = await crud_user.get_by_email(db=session, email=user_data["email"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first.",
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


@router.post("/social/register", response_model=AuthToken)
async def social_register(
    login_data: SocialLoginWithTokenData,
    session: AsyncSession = Depends(get_session),
):
    """
    소셜 회원가입 (신규 사용자)

    - 약관 동의 후 소셜 계정으로 회원가입합니다.
    - 이미 가입된 계정이 있으면 400 에러가 발생합니다.
    """
    oauth_client = get_oauth_client(login_data.provider)

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

    # 기존 사용자 확인
    existing_user = await crud_user.get_by_email(db=session, email=user_data["email"])

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists. Please login instead.",
        )

    # 신규 사용자 생성
    user = await crud_user.create_social_user(
        db=session,
        email=user_data["email"],
        nickname=user_data["name"],
        phone_number=user_data["mobile"],
        provider=login_data.provider,
        user_type=UserTypeEnum.social,
        gender=user_data["gender"],
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


@router.post("/guest-login", response_model=AuthToken)
async def guest_login(
    session: AsyncSession = Depends(get_session),
):
    """게스트 로그인 (비회원)"""
    nickname = generate_guest_nickname()
    user = await crud_user.create_guest_user(db=session, nickname=nickname)

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
