# src/schemas/user.py
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from core.enums import SocialProviderEnum
from utils.utils import utc_now


class UserBase(SQLModel):
    """공통 사용자 필드"""

    email: EmailStr | None = Field(default=None, max_length=255)
    phone_number: str = Field(..., max_length=20)
    nickname: str | None = Field(default=None, max_length=20)

    # 상태 관련 필드
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_deleted: bool = Field(default=False)

    # 동의 관련 필드
    service_policy_agreement: bool = Field(default=False)
    privacy_policy_agreement: bool = Field(default=False)
    third_party_information_agreement: bool = Field(default=False)

    # 소셜 로그인 관련
    social_provider: SocialProviderEnum = Field(default=SocialProviderEnum.naver)

    # 시간 관련
    joined_datetime: datetime


class User(UserBase, table=True):
    """데이터베이스 모델"""

    id: int | None = Field(default=None, primary_key=True)


class UserCreate(SQLModel):
    """사용자 생성 스키마"""

    email: EmailStr | None = Field(..., max_length=255)
    phone_number: str = Field(..., max_length=20)
    is_active: bool = Field(default=True)
    social_provider: SocialProviderEnum = Field(default=SocialProviderEnum.naver)
    joined_datetime: datetime = Field(default_factory=utc_now)
    is_superuser: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone_number": "01012345678",
                "social_provider": "naver",
            }
        }


class UserUpdate(SQLModel):
    """사용자 업데이트 스키마"""

    nickname: str | None = Field(default=None, max_length=20)
    service_policy_agreement: bool | None = Field(default=None)
    privacy_policy_agreement: bool | None = Field(default=None)
    third_party_information_agreement: bool | None = Field(default=None)
    updated_datetime: datetime = Field(default_factory=utc_now)

    class Config:
        json_schema_extra = {
            "example": {"nickname": "새로운닉네임", "service_policy_agreement": True}
        }


class UserRead(UserBase):
    """사용자 조회 응답 스키마"""

    id: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "phone_number": "01012345678",
                "nickname": "사용자",
                "is_active": True,
                "social_provider": "naver",
                "joined_datetime": "2024-02-08T00:00:00Z",
            }
        }


class UserDelete(SQLModel):
    """사용자 삭제 스키마"""

    id: int

    class Config:
        json_schema_extra = {"example": {"id": 1}}
