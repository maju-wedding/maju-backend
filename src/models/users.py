from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from core.enums import SocialProviderEnum
from utils.utils import utc_now


class UserBase(SQLModel):
    email: EmailStr = Field(index=True, max_length=255)
    phone_number: str = Field(..., max_length=20)
    is_active: bool = Field(default=True)
    service_policy_agreement: bool = Field(default=False)
    privacy_policy_agreement: bool = Field(default=False)
    third_party_information_agreement: bool = Field(default=False)
    nickname: str | None = Field(default=None, max_length=20)
    social_provider: SocialProviderEnum = Field(default=SocialProviderEnum.naver)
    joined_datetime: datetime


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class UserCreate(SQLModel):
    email: EmailStr = Field(..., max_length=255)
    phone_number: str = Field(..., max_length=20)
    is_active: bool = Field(default=True)
    social_provider: SocialProviderEnum = Field(default=SocialProviderEnum.naver)
    joined_datetime: datetime = Field(default_factory=utc_now)


class UserUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=20)
    service_policy_agreement: bool | None = Field(default=None)
    privacy_policy_agreement: bool | None = Field(default=None)
    third_party_information_agreement: bool | None = Field(default=None)
    updated_datetime: datetime = Field(default_factory=utc_now)


class UserRead(UserBase):
    id: int


class UserDelete(SQLModel):
    id: int
