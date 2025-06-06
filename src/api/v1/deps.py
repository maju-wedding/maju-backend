from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Security, status
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import and_

from core import security
from core.config import settings
from core.db import get_session
from core.enums import UserTypeEnum
from core.oauth_client import OAuthClient, kakao_client, naver_client
from core.security import oauth2_scheme
from models.users import User
from schemes.auth import AuthTokenPayload


def verify_jwt_token(token: str = Security(oauth2_scheme)) -> str:
    return token


async def get_current_user(
    token: Annotated[str, Depends(verify_jwt_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = AuthTokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user_type = token_data.type

    if user_type == UserTypeEnum.guest:
        # 게스트 사용자는 UUID로 조회
        try:
            user_id = UUID(token_data.sub)
            query = select(User).where(User.id == user_id)
            result = await session.stream(query)
            user = await result.scalar_one_or_none()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user ID format",
            )
    else:
        # 일반/소셜 사용자는 이메일로 조회
        query = select(User).where(
            and_(
                User.email == token_data.sub,
                User.is_deleted == False,
            )
        )
        result = await session.stream(query)
        user = await result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def get_oauth_client(provider: str) -> OAuthClient:
    if provider == "naver":
        return naver_client
    elif provider == "kakao":
        return kakao_client
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
