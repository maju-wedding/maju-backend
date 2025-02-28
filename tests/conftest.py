import asyncio
import uuid
from datetime import timedelta
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from core.config import settings
from core.db import get_session
from core.enums import UserTypeEnum, CategoryTypeEnum, SocialProviderEnum
from core.security import create_access_token, get_password_hash
from main import app
from models import Category
from models.checklist import SuggestChecklist, UserChecklist
from models.users import User

# 테스트용 엔진 및 세션 생성
test_engine = create_async_engine(
    settings.DATABASE_URI,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    # 테이블 생성
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # 테스트 후 테이블 삭제
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(setup_database, db_session) -> AsyncGenerator[AsyncClient, None]:
    def get_session_override():
        return db_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client
        app.dependency_overrides.clear()


# 테스트 유저 생성
@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    # 로컬 사용자 생성
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone_number="01012345678",  # 필수 필드 추가
        nickname="테스트유저",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
        user_type=UserTypeEnum.local.value,  # local 유저로 변경
        service_policy_agreement=True,
        privacy_policy_agreement=True,
        third_party_information_agreement=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


# 소셜 로그인 유저 생성
@pytest_asyncio.fixture(scope="function")
async def test_social_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="social@example.com",
        phone_number="01087654321",
        nickname="소셜유저",
        is_active=True,
        user_type=UserTypeEnum.social.value,
        social_provider=SocialProviderEnum.kakao,
        service_policy_agreement=True,
        privacy_policy_agreement=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


# 게스트 유저 생성
@pytest_asyncio.fixture(scope="function")
async def test_guest_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone_number="01011112222",  # 게스트는 이메일 없음
        is_active=True,
        user_type=UserTypeEnum.guest.value,
        service_policy_agreement=True,
        privacy_policy_agreement=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def test_user_token(test_user: User) -> str:
    # 로컬 유저는 이메일로 토큰 생성
    return create_access_token(
        subject=test_user.email,
        user_type=UserTypeEnum.local,
        expires_delta=timedelta(days=1),  # 1일
        extra_claims={"nickname": test_user.nickname},
    )


@pytest.fixture(scope="function")
def test_guest_token(test_guest_user: User) -> str:
    # 게스트 유저는 UUID로 토큰 생성
    return create_access_token(
        subject=str(test_guest_user.id),
        user_type=UserTypeEnum.guest,
        expires_delta=timedelta(days=1),  # 1일
        extra_claims={"nickname": test_guest_user.nickname},
    )


@pytest_asyncio.fixture(scope="function")
async def authorized_client(
    async_client: AsyncClient, test_user_token: str
) -> AsyncClient:
    async_client.headers = {
        "Authorization": f"Bearer {test_user_token}",
        **async_client.headers,
    }
    return async_client


@pytest_asyncio.fixture(scope="function")
async def guest_authorized_client(
    async_client: AsyncClient, test_guest_token: str
) -> AsyncClient:
    async_client.headers = {
        "Authorization": f"Bearer {test_guest_token}",
        **async_client.headers,
    }
    return async_client


# 카테고리 데이터 생성
@pytest_asyncio.fixture(scope="function")
async def categories(db_session: AsyncSession):
    categories = [
        Category(
            id=1,
            name="웨딩홀",
            type=CategoryTypeEnum.hall.value,
            display_name="웨딩홀",
            is_ready=True,
            order=1,
        ),
        Category(
            id=2,
            name="스튜디오",
            type=CategoryTypeEnum.studio.value,
            display_name="스튜디오",
            is_ready=True,
            order=2,
        ),
        Category(
            id=3,
            name="드레스",
            type=CategoryTypeEnum.dress.value,
            display_name="드레스",
            is_ready=True,
            order=3,
        ),
        Category(
            id=4,
            name="메이크업",
            type=CategoryTypeEnum.makeup.value,
            display_name="메이크업",
            is_ready=True,
            order=4,
        ),
    ]

    for category in categories:
        db_session.add(category)

    await db_session.commit()

    return categories


# 추천 체크리스트 생성
@pytest_asyncio.fixture(scope="function")
async def suggest_checklists(
    db_session: AsyncSession, categories: list[Category]
) -> list[SuggestChecklist]:
    checklists = [
        SuggestChecklist(
            title=f"추천 체크리스트 {i}",
            description=f"추천 체크리스트 {i}에 대한 설명",
            category_id=i % 4 + 1,  # 4개의 카테고리에 맞춰 조정
            order=i,
        )
        for i in range(1, 6)  # 5개의 추천 체크리스트 생성
    ]

    for checklist in checklists:
        db_session.add(checklist)

    await db_session.commit()

    for checklist in checklists:
        await db_session.refresh(checklist)

    return checklists


# 사용자 체크리스트 생성
@pytest_asyncio.fixture(scope="function")
async def user_checklists(
    db_session: AsyncSession,
    test_user: User,
    suggest_checklists: list[SuggestChecklist],
) -> list[UserChecklist]:
    checklists = []

    # 추천 체크리스트 기반 항목 추가
    for i, suggest in enumerate(suggest_checklists[:3]):  # 처음 3개만 추가
        checklist = UserChecklist(
            title=suggest.title,
            description=suggest.description,
            suggest_item_id=suggest.id,
            user_id=test_user.id,
            category_id=suggest.checklist_category_id,
            is_completed=False,  # 짝수 번째 항목은 완료 상태로
            order=i,
        )
        checklists.append(checklist)

    # 사용자 정의 체크리스트 추가
    for i in range(2):
        checklist = UserChecklist(
            title=f"사용자 정의 체크리스트 {i+1}",
            description=f"사용자 정의 체크리스트 {i+1}에 대한 설명",
            user_id=test_user.id,
            category_id=(i % 4) + 1,  # 4개의 카테고리에 맞춰 조정
            suggest_item_id=None,  # 사용자 정의 항목은 추천 ID가 없음
            is_completed=False,
            order=i + 3,  # 추천 항목 이후부터 순서 지정
        )
        checklists.append(checklist)

    for checklist in checklists:
        db_session.add(checklist)

    await db_session.commit()

    for checklist in checklists:
        await db_session.refresh(checklist)

    return checklists


# 게스트 사용자의 체크리스트 생성
@pytest_asyncio.fixture(scope="function")
async def guest_checklists(
    db_session: AsyncSession,
    test_guest_user: User,
    suggest_checklists: list[SuggestChecklist],
) -> list[UserChecklist]:
    checklists = []

    # 게스트 사용자를 위한 체크리스트 생성
    for i, suggest in enumerate(suggest_checklists[:2]):  # 처음 2개만 추가
        checklist = UserChecklist(
            title=suggest.title,
            description=suggest.description,
            suggest_item_id=suggest.id,
            user_id=test_guest_user.id,
            category_id=suggest.checklist_category_id,
            is_completed=False,
            order=i,
        )
        checklists.append(checklist)

    for checklist in checklists:
        db_session.add(checklist)

    await db_session.commit()

    for checklist in checklists:
        await db_session.refresh(checklist)

    return checklists
