from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security.http import HTTPBearer
from jwt.exceptions import InvalidTokenError
from models.auth import AuthTokenPayload
from models.users import User
from pydantic import ValidationError
from sqlmodel import Session

from core import security
from core.config import settings
from core.db import engine
from core.oauth_client import OAuthClient, kakao_client, naver_client
from cruds import users as users_crud


def verify_jwt_token(
    access_token=Security(HTTPBearer(auto_error=True)),
) -> str:
    return access_token.credentials


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(verify_jwt_token)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
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

    user = await users_crud.get_user_by_email(session=session, email=token_data.sub)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_oauth_client(provider: str = Query(..., regex="naver|kakao")) -> OAuthClient:
    if provider == "naver":
        return naver_client
    elif provider == "kakao":
        return kakao_client
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
