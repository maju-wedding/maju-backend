from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from core.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
    future=True,
    # Connection Pool 설정
    pool_size=10,  # 기본 연결 수
    max_overflow=20,  # 추가로 생성 가능한 연결 수
    pool_pre_ping=True,  # 연결 재사용 전 health check
    pool_recycle=3600,  # 1시간마다 연결 재생성
    pool_timeout=30,  # 연결 대기 시간 (초)

    # 연결 옵션 최적화
    connect_args={
        "command_timeout": 30,
        "server_settings": {
            "application_name": "serenade_api",
            "jit": "off",  # JIT 컴파일 비활성화 (연결 속도 향상)
        },
    },
)

async_session = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        async with async_session() as session:
            await session.stream(text("SELECT 1"))
            return True
    except Exception as e:
        print(e)
        return False


# 애플리케이션 종료 시 정리
async def close_db_connections():
    """데이터베이스 연결 정리"""
    await async_engine.dispose()
