import asyncio
import argparse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.config import settings
from core.security import get_password_hash
from core.enums import UserTypeEnum
from models.users import User
from utils.utils import utc_now


async def create_superuser(email, password, nickname, phone_number):
    """Create a superuser for accessing the admin dashboard."""
    engine = create_async_engine(settings.DATABASE_URI)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        result = await session.executeute(stmt)
        user = result.scalar_one_or_none()

        if user:
            if user.is_superuser:
                print(f"Superuser {email} already exists.")
                return

            # Update existing user to superuser
            user.is_superuser = True
            user.updated_datetime = utc_now()
            session.add(user)
            await session.commit()
            print(f"User {email} has been updated to superuser.")
            return

        # Create new superuser
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            nickname=nickname,
            phone_number=phone_number,
            user_type=UserTypeEnum.local,
            is_superuser=True,
            is_active=True,
        )

        session.add(new_user)
        await session.commit()
        print(f"Superuser {email} created successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a superuser for the admin dashboard"
    )
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--nickname", required=True, help="Nickname")
    parser.add_argument("--phone", required=True, help="Phone number")

    args = parser.parse_args()

    asyncio.run(create_superuser(args.email, args.password, args.nickname, args.phone))
