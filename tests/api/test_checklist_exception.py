import uuid
from datetime import timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from core.enums import UserTypeEnum

BASE_URL = "/api/v1/checklist"


# 인증되지 않은 사용자 테스트
@pytest.mark.asyncio
async def test_unauthenticated_access(async_client: AsyncClient):
    # 인증 없이 사용자 체크리스트 접근 시도
    response = await async_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# 다른 사용자의 체크리스트 수정 시도 테스트
@pytest.mark.asyncio
async def test_update_other_users_checklist(
    authorized_client: AsyncClient, db_session, suggest_checklists
):
    # 다른 사용자 생성
    from models.users import User

    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        phone_number="01099998888",
        nickname="다른유저",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        user_type=UserTypeEnum.local.value,
        service_policy_agreement=True,
        privacy_policy_agreement=True,
    )

    db_session.add(other_user)
    await db_session.commit()

    # 다른 사용자의 체크리스트 생성
    from models.checklist import UserChecklist

    other_checklist = UserChecklist(
        title="다른 사용자의 체크리스트",
        description="이 체크리스트는 다른 사용자의 것입니다",
        user_id=other_user.id,
        suggest_item_id=suggest_checklists[0].id,
        category_id=1,
    )

    db_session.add(other_checklist)
    await db_session.commit()
    await db_session.refresh(other_checklist)

    # 현재 인증된 사용자로 다른 사용자의 체크리스트 수정 시도
    update_data = {
        "title": "수정 시도",
        "description": "권한이 없는 수정 시도",
    }

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/{other_checklist.id}", json=update_data
    )

    # 체크리스트가 존재하지만 현재 사용자의 것이 아니기 때문에 404 반환
    assert response.status_code == status.HTTP_404_NOT_FOUND


# 비활성화된 사용자의 체크리스트 접근 테스트
@pytest.mark.asyncio
async def test_inactive_user_access(db_session, async_client, suggest_checklists):
    # 비활성화된 사용자 생성
    from models.users import User
    from core.security import create_access_token

    inactive_user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        phone_number="01077776666",
        is_active=False,  # 비활성화 상태
        user_type=UserTypeEnum.local.value,
        hashed_password="hashed_password",
        service_policy_agreement=True,
        privacy_policy_agreement=True,
    )

    db_session.add(inactive_user)
    await db_session.commit()

    # 비활성화된 사용자의 토큰 생성
    inactive_token = create_access_token(
        subject=inactive_user.email,
        user_type=UserTypeEnum.local,
        expires_delta=timedelta(days=1),
    )

    # 헤더에 토큰 설정
    async_client.headers = {
        "Authorization": f"Bearer {inactive_token}",
        **async_client.headers,
    }

    # 체크리스트 접근 시도
    response = await async_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Inactive user" in response.json()["detail"]


# 잘못된 체크리스트 정렬 요청 테스트
@pytest.mark.asyncio
async def test_invalid_checklist_order_request(
    authorized_client: AsyncClient, user_checklists
):
    # 하나의 체크리스트 ID는 실제로 존재하고 다른 하나는 존재하지 않음
    order_updates = [
        {"id": user_checklists[0].id, "order": 1},
        {"id": 9999, "order": 2},  # 존재하지 않는 ID
    ]

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/order", json=order_updates
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# 카테고리 필터링 시 존재하지 않는 카테고리 테스트
@pytest.mark.asyncio
async def test_nonexistent_category_filter(authorized_client: AsyncClient):
    nonexistent_category = 999

    response = await authorized_client.get(
        f"{BASE_URL}/user-checklist?category_id={nonexistent_category}"
    )
    assert response.status_code == status.HTTP_200_OK

    # 존재하지 않는 카테고리이므로 결과가 비어있어야 함
    data = response.json()
    assert len(data) == 0


# 게스트 사용자가 다른 사용자의 체크리스트에 접근 시도
@pytest.mark.asyncio
async def test_guest_access_other_users_checklist(
    guest_authorized_client: AsyncClient, user_checklists
):
    # 일반 사용자의 체크리스트 ID로 접근 시도
    checklist_id = user_checklists[0].id

    response = await guest_authorized_client.put(
        f"{BASE_URL}/user-checklists/{checklist_id}",
        json={"title": "게스트의 수정 시도"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# 체크리스트 개수 제한 테스트 (대량 추가)
@pytest.mark.asyncio
async def test_bulk_checklist_creation(
    authorized_client: AsyncClient, suggest_checklists, db_session
):
    # 20개의 체크리스트 추가 시도 (API가 이를 제한하는지 테스트)
    # 동일한 추천 체크리스트를 여러 번 추가
    # 실제 API에서 제한 사항이 있을 경우 조정이 필요합니다
    suggest_ids = [suggest_checklists[0].id] * 20

    response = await authorized_client.post(
        f"{BASE_URL}/user-checklists", json=suggest_ids
    )

    # 정상적으로 처리되거나 제한에 걸리는 경우 확인
    # (실제 API 사양에 따라 예상 결과가 달라질 수 있음)
    if response.status_code == status.HTTP_200_OK:
        # 제한이 없는 경우
        data = response.json()
        assert len(data) == 20
    else:
        # 제한이 있는 경우 - 적절한 오류 코드 확인
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


# 체크리스트의 유효한 필드만 업데이트 테스트
@pytest.mark.asyncio
async def test_update_checklist_valid_fields_only(
    authorized_client: AsyncClient, user_checklists
):
    checklist_id = user_checklists[0].id

    # 유효한 필드와 유효하지 않은 필드를 모두 포함
    update_data = {
        "title": "유효한 제목 업데이트",
        "description": "유효한 설명 업데이트",
        "invalid_field": "이 필드는 무시되어야 함",
        "another_invalid": 123,
    }

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/{checklist_id}", json=update_data
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 유효한 필드만 업데이트되었는지 확인
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    # 유효하지 않은 필드는 응답에 포함되지 않아야 함
    assert "invalid_field" not in data
    assert "another_invalid" not in data
