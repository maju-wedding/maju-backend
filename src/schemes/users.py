from datetime import datetime
from uuid import UUID

import sqlmodel
from pydantic import EmailStr, SecretStr
from sqlmodel import SQLModel, Field

from core.enums import UserTypeEnum, SocialProviderEnum, GenderEnum
from utils.utils import utc_now


class UserCreate(SQLModel):
    """자체 회원가입 전용 스키마"""

    nickname: str = Field(max_length=20)
    email: EmailStr = Field(..., max_length=255)
    phone_number: str = Field(..., max_length=20)
    password: SecretStr = Field(...)

    is_active: bool = Field(default=True)
    user_type: UserTypeEnum = Field(default=UserTypeEnum.local)
    social_provider: SocialProviderEnum | None = Field(default=None)
    joined_datetime: datetime = Field(default_factory=utc_now)

    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "user",
                "email": "user@example.com",
                "phone_number": "01012345678",
                "password": "yourpassword",
            }
        }


class InternalUserCreate(SQLModel):
    """사용자 생성 전용 스키마"""

    nickname: str = Field(max_length=20)
    email: EmailStr | None = Field(None, max_length=255)
    phone_number: str | None = Field(None, max_length=20)
    hashed_password: str | None = Field(None)
    is_active: bool = Field(default=True)
    gender: GenderEnum | None = Field(default=None)

    joined_datetime: datetime = Field(default_factory=utc_now)
    social_provider: SocialProviderEnum | None = Field(default=None)
    user_type: UserTypeEnum


class UserUpdate(SQLModel):
    """사용자 업데이트 스키마"""

    nickname: str | None = Field(default=None, max_length=20)

    gender: GenderEnum | None = Field(default=None, max_length=10)
    wedding_datetime: datetime | None = Field(default=None)
    service_policy_agreement: bool | None = Field(default=None)
    privacy_policy_agreement: bool | None = Field(default=None)
    advertising_agreement: bool | None = Field(default=None)
    updated_datetime: datetime = Field(default_factory=utc_now)
    budget: int | None = Field(default=None, ge=0)


class UserRead(SQLModel):
    """사용자 조회 응답 스키마"""

    id: UUID
    email: EmailStr | None
    phone_number: str
    nickname: str

    user_type: UserTypeEnum
    social_provider: SocialProviderEnum | None

    joined_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True), default=utc_now),
    )


class UserDelete(SQLModel):
    """사용자 삭제 스키마"""

    id: UUID
