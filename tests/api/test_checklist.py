import uuid
from datetime import timedelta

from fastapi import status
from httpx import AsyncClient

from core.enums import UserTypeEnum
from core.security import create_access_token
from models import User
from models.checklist import UserChecklist

BASE_URL = "/api/v1/checklist"


# 추천 체크리스트 목록 테스트
async def test_list_suggest_checklists(
    authorized_client: AsyncClient, suggest_checklists
):
    response = await authorized_client.get(f"{BASE_URL}/suggest-items")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(suggest_checklists)


# 카테고리별 추천 체크리스트 필터링 테스트
async def test_list_suggest_checklists_with_category(
    authorized_client: AsyncClient, suggest_checklists
):
    category_id = 1
    response = await authorized_client.get(
        f"{BASE_URL}/suggest-items?category_id={category_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 모든 항목이 요청한 카테고리를 가지는지 확인
    for item in data:
        assert item["category_id"] == category_id


# 일반 사용자의 체크리스트 목록 테스트
async def test_list_user_checklists(authorized_client: AsyncClient, user_checklists):
    response = await authorized_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(user_checklists)


# 게스트 사용자의 체크리스트 목록 테스트
async def test_list_guest_checklists(
    guest_authorized_client: AsyncClient, guest_checklists
):
    response = await guest_authorized_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(guest_checklists)


# 카테고리별 사용자 체크리스트 필터링 테스트
async def test_list_user_checklists_with_category(
    authorized_client: AsyncClient, user_checklists
):
    category_id = 1
    response = await authorized_client.get(
        f"{BASE_URL}/user-checklist?category_id={category_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 모든 항목이 요청한 카테고리를 가지는지 확인
    for item in data:
        assert item["category_id"] == category_id


# 완료된 사용자 체크리스트 필터링 테스트
async def test_list_completed_user_checklists(
    authorized_client: AsyncClient, user_checklists
):
    response = await authorized_client.get(
        f"{BASE_URL}/user-checklist?completed_only=true"
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 모든 항목이 완료 상태인지 확인
    for item in data:
        assert item["is_completed"] == True

    # 완료된 항목 수 확인
    completed_count = sum(1 for item in user_checklists if item.is_completed)
    assert len(data) == completed_count


# 추천 체크리스트를 사용자 체크리스트로 추가하는 테스트
async def test_create_user_checklists_from_suggestions(
    authorized_client: AsyncClient, suggest_checklists
):
    # 모든 추천 체크리스트 ID 가져오기
    suggest_ids = [item.id for item in suggest_checklists]

    response = await authorized_client.post(
        f"{BASE_URL}/user-checklists", json=suggest_ids
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(suggest_ids)

    # 생성된 항목이 올바른 suggest_item_id를 가지는지 확인
    created_suggest_ids = [item["suggest_item_id"] for item in data]
    for suggest_id in suggest_ids:
        assert suggest_id in created_suggest_ids


# 게스트 사용자가 추천 체크리스트를 추가하는 테스트
async def test_guest_create_user_checklists_from_suggestions(
    guest_authorized_client: AsyncClient, suggest_checklists
):
    # 모든 추천 체크리스트 ID 가져오기
    suggest_ids = [item.id for item in suggest_checklists[:2]]  # 처음 2개만 선택

    response = await guest_authorized_client.post(
        f"{BASE_URL}/user-checklists", json=suggest_ids
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(suggest_ids)


# 사용자 정의 체크리스트 생성 테스트
async def test_create_custom_checklist(authorized_client: AsyncClient):
    new_checklist = {
        "title": "테스트 체크리스트",
        "description": "API로 생성된 테스트 체크리스트",
        "category_id": 1,
    }

    response = await authorized_client.post(
        f"{BASE_URL}/custom-checklists", json=new_checklist
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == new_checklist["title"]
    assert data["description"] == new_checklist["description"]
    assert data["category_id"] == new_checklist["category_id"]
    assert data["is_completed"] == False  # 새 체크리스트는 완료되지 않은 상태여야 함


# 사용자 체크리스트 업데이트 테스트
async def test_update_user_checklist(authorized_client: AsyncClient, user_checklists):
    checklist_id = user_checklists[0].id
    update_data = {
        "title": "수정된 제목",
        "description": "수정된 설명",
        "is_completed": True,
    }

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/{checklist_id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == checklist_id
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["is_completed"] == update_data["is_completed"]
    assert data["completed_datetime"] is not None  # 완료 시간이 설정되어야 함


# 게스트 사용자 체크리스트 업데이트 테스트
async def test_guest_update_checklist(
    guest_authorized_client: AsyncClient, guest_checklists
):
    checklist_id = guest_checklists[0].id
    update_data = {"title": "게스트가 수정한 제목", "is_completed": True}

    response = await guest_authorized_client.put(
        f"{BASE_URL}/user-checklists/{checklist_id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["is_completed"] == update_data["is_completed"]


# 사용자 체크리스트 삭제 테스트 (소프트 삭제)
async def test_delete_user_checklist(
    authorized_client: AsyncClient, user_checklists, db_session
):
    checklist_id = user_checklists[0].id

    response = await authorized_client.delete(
        f"{BASE_URL}/user-checklists/{checklist_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    # DB에서 소프트 삭제 확인
    result = await db_session.get(UserChecklist, checklist_id)
    assert result.is_deleted == True

    # 삭제된 항목이 목록에서 제외되는지 확인
    list_response = await authorized_client.get(f"{BASE_URL}/user-checklist")
    data = list_response.json()
    deleted_items = [item for item in data if item["id"] == checklist_id]
    assert len(deleted_items) == 0


# 체크리스트 순서 업데이트 테스트
async def test_update_checklists_order(authorized_client: AsyncClient, user_checklists):
    order_updates = [
        {"id": user_checklists[0].id, "order": 5},
        {"id": user_checklists[1].id, "order": 4},
        {"id": user_checklists[2].id, "order": 3},
    ]

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/order", json=order_updates
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # 순서가 올바르게 업데이트되었는지 확인
    for i, update in enumerate(order_updates):
        found = False
        for item in data:
            if item["id"] == update["id"]:
                assert item["order"] == update["order"]
                found = True
                break
        assert found, f"ID {update['id']}를 가진 항목을 찾을 수 없습니다"


# 카테고리별 체크리스트 필터링 및 정렬 테스트
async def test_list_checklists_with_category_and_order(
    authorized_client: AsyncClient, user_checklists
):
    # 먼저 순서 업데이트
    order_updates = [
        {"id": user_checklists[0].id, "order": 3},
        {"id": user_checklists[1].id, "order": 1},
        {"id": user_checklists[2].id, "order": 2},
    ]

    response = await authorized_client.put(
        f"{BASE_URL}/user-checklists/order", json=order_updates
    )

    assert response.status_code == status.HTTP_200_OK

    # 특정 카테고리로 필터링
    category_id = user_checklists[0].category_id
    response = await authorized_client.get(
        f"{BASE_URL}/user-checklist?category_id={category_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # 해당 카테고리의 체크리스트만 포함되어 있는지 확인
    for item in data:
        assert item["category_id"] == category_id

    if len(data) > 1:
        for i in range(len(data) - 1):
            assert data[i]["order"] <= data[i + 1]["order"]


# 인증되지 않은 사용자 테스트
async def test_unauthenticated_access(async_client: AsyncClient):
    # 인증 없이 사용자 체크리스트 접근 시도
    response = await async_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# 다른 사용자의 체크리스트 수정 시도 테스트
async def test_update_other_users_checklist(
    authorized_client: AsyncClient, db_session, suggest_checklists
):
    # 다른 사용자 생성
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        phone_number="01099998888",
        nickname="다른유저",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        user_type=UserTypeEnum.local,
        service_policy_agreement=True,
        privacy_policy_agreement=True,
    )

    db_session.add(other_user)
    await db_session.commit()

    # 다른 사용자의 체크리스트 생성
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
async def test_inactive_user_access(db_session, async_client, suggest_checklists):
    # 비활성화된 사용자 생성
    inactive_user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        phone_number="01077776666",
        is_active=False,  # 비활성화 상태
        user_type=UserTypeEnum.local,
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
async def test_bulk_checklist_creation(
    authorized_client: AsyncClient, suggest_checklists, db_session
):
    # 20개의 같은 체크리스트 추가 시도
    suggest_ids = [suggest_checklists[0].id] * 20

    response = await authorized_client.post(
        f"{BASE_URL}/user-checklists", json=suggest_ids
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1


# 체크리스트의 유효한 필드만 업데이트 테스트
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
