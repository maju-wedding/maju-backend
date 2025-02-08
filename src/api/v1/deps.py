from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security.http import HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core import security
from core.config import settings
from core.db import get_session
from core.oauth_client import OAuthClient, kakao_client, naver_client
from cruds.crud_users import user_crud
from models.auth import AuthTokenPayload
from models.users import User


def verify_jwt_token(
    access_token=Security(HTTPBearer(auto_error=True)),
) -> str:
    return access_token.credentials


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

    user = await user_crud.get(session, email=token_data.sub)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


def get_oauth_client(provider: str = Query(..., regex="naver|kakao")) -> OAuthClient:
    if provider == "naver":
        return naver_client
    elif provider == "kakao":
        return kakao_client
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
