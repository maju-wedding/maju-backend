from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import UserTypeEnum, GenderEnum, SocialProviderEnum
from core.security import get_password_hash, verify_password
from models.users import User
from schemes.users import UserCreate, UserUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate, UUID]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Get a user by email"""
        query = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False,
                User.is_active == True,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_by_phone_number(
        self, db: AsyncSession, *, phone_number: str
    ) -> User | None:
        """Get a user by phone number"""
        query = select(User).where(
            and_(
                User.phone_number == phone_number,
                User.is_deleted == False,
                User.is_active == True,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password"""
        db_obj = User(
            email=obj_in.email,
            hashed_password=(
                get_password_hash(obj_in.password.get_secret_value())
                if hasattr(obj_in, "password")
                else None
            ),
            nickname=obj_in.nickname,
            phone_number=obj_in.phone_number,
            user_type=obj_in.user_type,
            social_provider=getattr(obj_in, "social_provider", None),
            is_active=True,
            joined_datetime=utc_now(),
            updated_datetime=utc_now(),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        """Update user with password handling"""
        update_data = obj_in.model_dump(exclude_unset=True)
        if hasattr(obj_in, "password") and obj_in.password:
            hashed_password = get_password_hash(obj_in.password.get_secret_value())
            update_data["hashed_password"] = hashed_password
            del update_data["password"]

        update_data["updated_datetime"] = utc_now()
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User | None:
        """Authenticate user by email and password"""
        user = await self.get_by_email(db, email=email)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_social_user(
        self,
        db: AsyncSession,
        *,
        email: str,
        nickname: str,
        phone_number: str,
        provider: SocialProviderEnum,
        user_type: UserTypeEnum = UserTypeEnum.social,
        gender: GenderEnum = None
    ) -> User:
        """Create a social login user"""
        db_obj = User(
            email=email,
            nickname=nickname,
            phone_number=phone_number,
            social_provider=provider,
            user_type=user_type,
            gender=gender,
            is_active=True,
            joined_datetime=utc_now(),
            updated_datetime=utc_now(),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_guest_user(self, db: AsyncSession, *, nickname: str) -> User:
        """Create a guest user with generated nickname"""
        db_obj = User(
            nickname=nickname,
            user_type=UserTypeEnum.guest,
            is_active=True,
            joined_datetime=utc_now(),
            updated_datetime=utc_now(),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
