from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel

from core.enums import UserTypeEnum, SocialProviderEnum


class SocialLoginWithTokenData(SQLModel):
    access_token: str
    provider: SocialProviderEnum


class AuthToken(SQLModel):
    access_token: str
    token_type: str = "bearer"
    nickname: str | None


class AuthTokenPayload(SQLModel):
    sub: str
    exp: datetime
    type: UserTypeEnum
    iat: datetime
    nickname: str | None = None


class LoginRequest(SQLModel):
    email: EmailStr
    password: str


class SocialUserCheckResponse(SQLModel):
    exists: bool
