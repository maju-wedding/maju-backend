from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlmodel
from pydantic import EmailStr
from sqlalchemy import Column, String, Boolean
from sqlmodel import Field, SQLModel, Relationship

from core.enums import SocialProviderEnum, UserTypeEnum, GenderEnum
from utils.utils import utc_now

if TYPE_CHECKING:
    from models import UserSpent
    from models.checklists import Checklist


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    hashed_password: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(..., max_length=20)
    nickname: str = Field(..., max_length=20)
    gender: GenderEnum | None = Field(
        None, max_length=10, sa_column=Column(String, nullable=True)
    )
    wedding_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    budget: int = Field(default=0)

    user_type: UserTypeEnum = Field(
        default=UserTypeEnum.guest,
        sa_column=Column(String, default=UserTypeEnum.guest.value),
    )
    social_provider: SocialProviderEnum | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )

    service_policy_agreement: bool | None = Field(
        default=False, sa_column=Column(Boolean, default=False)
    )
    privacy_policy_agreement: bool | None = Field(
        default=False, sa_column=Column(Boolean, default=False)
    )
    advertising_agreement: bool | None = Field(
        default=False, sa_column=Column(Boolean, default=False)
    )

    joined_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True), default=utc_now),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True), default=utc_now),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )

    is_superuser: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, default=True))
    is_deleted: bool = Field(default=False, sa_column=Column(Boolean, default=False))

    # Relationships
    user_spents: list["UserSpent"] = Relationship(back_populates="user")
    checklists: list["Checklist"] = Relationship(
        back_populates="user"
    )  # Checklist 관계 추가
