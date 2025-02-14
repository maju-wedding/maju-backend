from datetime import datetime
from uuid import UUID, uuid4

import sqlmodel
from pydantic import EmailStr, SecretStr
from sqlalchemy import Column
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel

from core.enums import SocialProviderEnum, UserTypeEnum
from utils.utils import utc_now


class UserBase(SQLModel):
    """공통 사용자 필드"""

    email: EmailStr | None = Field(default=None, max_length=255)
    phone_number: str = Field(..., max_length=20)
    nickname: str | None = Field(default=None, max_length=20)

    # 상태 관련 필드
    is_active: bool = Field(default=True)

    # 사용자 타입 구분
    user_type: UserTypeEnum = Field(
        default=UserTypeEnum.guest,
        sa_column=Column(postgresql.ENUM(UserTypeEnum)),
    )
    social_provider: SocialProviderEnum | None = Field(default=None)

    # 동의 관련 필드
    service_policy_agreement: bool = Field(default=False)
    privacy_policy_agreement: bool = Field(default=False)
    third_party_information_agreement: bool = Field(default=False)

    # 시간 관련
    joined_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True), default=utc_now),
    )


class User(UserBase, table=True):
    """데이터베이스 모델"""

    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    hashed_password: str | None = Field(default=None, max_length=255)
    is_superuser: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


class UserCreate(SQLModel):
    """사용자 생성 스키마"""

    email: EmailStr = Field(..., max_length=255)
    phone_number: str = Field(..., max_length=20)
    password: SecretStr | None = None  # 자체 회원가입시에만 필요
    is_active: bool = Field(default=True)
    user_type: UserTypeEnum = Field(default=UserTypeEnum.guest)
    social_provider: SocialProviderEnum | None = None
    joined_datetime: datetime = Field(default_factory=utc_now)


class UserCreateLocal(UserCreate):
    """자체 회원가입 전용 스키마"""

    password: SecretStr = Field(...)  # 필수 필드로 변경
    user_type: UserTypeEnum = Field(default=UserTypeEnum.local)


class UserCreateSocial(UserCreate):
    """소셜 회원가입 전용 스키마"""

    social_provider: SocialProviderEnum = Field(...)
    user_type: UserTypeEnum = Field(default=UserTypeEnum.social)


class UserCreateGuest(UserCreate):
    """게스트 회원가입 전용 스키마"""

    user_type: UserTypeEnum = Field(default=UserTypeEnum.guest)


class UserUpdate(SQLModel):
    """사용자 업데이트 스키마"""

    nickname: str | None = Field(default=None, max_length=20)
    service_policy_agreement: bool | None = Field(default=None)
    privacy_policy_agreement: bool | None = Field(default=None)
    third_party_information_agreement: bool | None = Field(default=None)
    updated_datetime: datetime = Field(default_factory=utc_now)


class UserRead(UserBase):
    """사용자 조회 응답 스키마"""

    id: UUID


class UserDelete(SQLModel):
    """사용자 삭제 스키마"""

    id: UUID
