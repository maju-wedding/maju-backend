import pytest
from fastapi import status
from httpx import AsyncClient

from models.checklist import UserChecklist

BASE_URL = "/api/v1/checklist"


# 추천 체크리스트 목록 테스트
@pytest.mark.asyncio
async def test_list_suggest_checklists(
    authorized_client: AsyncClient, suggest_checklists
):
    response = await authorized_client.get(f"{BASE_URL}/suggest-items")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(suggest_checklists)


# 카테고리별 추천 체크리스트 필터링 테스트
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def test_list_user_checklists(authorized_client: AsyncClient, user_checklists):
    response = await authorized_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(user_checklists)


# 게스트 사용자의 체크리스트 목록 테스트
@pytest.mark.asyncio
async def test_list_guest_checklists(
    guest_authorized_client: AsyncClient, guest_checklists
):
    response = await guest_authorized_client.get(f"{BASE_URL}/user-checklist")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == len(guest_checklists)


# 카테고리별 사용자 체크리스트 필터링 테스트
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
    assert data["completed_at"] is not None  # 완료 시간이 설정되어야 함


# 게스트 사용자 체크리스트 업데이트 테스트
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def test_list_checklists_with_category_and_order(
    authorized_client: AsyncClient, user_checklists, db_session
):
    # 먼저 순서 업데이트
    order_updates = [
        {"id": user_checklists[0].id, "order": 3},
        {"id": user_checklists[1].id, "order": 1},
        {"id": user_checklists[2].id, "order": 2},
    ]

    await authorized_client.put(f"{BASE_URL}/user-checklists/order", json=order_updates)

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

    # 주어진 정렬 순서대로 정렬되어 있는지 확인 (API에서 정렬 기능 구현 필요)
    # 이 테스트는 API가 order 필드로 정렬하도록 구현되어 있다고 가정합니다
    if len(data) > 1:
        for i in range(len(data) - 1):
            assert data[i]["order"] <= data[i + 1]["order"]
