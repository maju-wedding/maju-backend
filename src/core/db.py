from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from core.config import settings

async_engine = create_async_engine(settings.DATABASE_URI, echo=True, future=True)

async_session = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession | Any, Any]:
    async with async_session() as session:
        yield session
