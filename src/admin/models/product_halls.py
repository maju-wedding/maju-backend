from typing import Any

from starlette.requests import Request

from admin.models.base import BaseModelViewWithFilters
from models import ProductHall


class ProductHallAdmin(BaseModelViewWithFilters, model=ProductHall):
    name = "웨딩홀"
    name_plural = "웨딩홀 목록"
    icon = "fa-solid fa-building"
    category = "상품 관리"

    column_list = [
        ProductHall.id,
        "product.name",
        "product.address",
        ProductHall.hall_type,
        ProductHall.hall_style,
        ProductHall.wedding_type,
        ProductHall.wedding_running_time,
        ProductHall.food_type,
        ProductHall.food_cost,
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.guaranteed_min_count,
        ProductHall.elevator,
        ProductHall.valet_parking,
        ProductHall.pyebaek_room,
        ProductHall.family_waiting_room,
        ProductHall.atm,
        ProductHall.dress_room,
        ProductHall.smoking_area,
        ProductHall.photo_zone,
        ProductHall.is_deleted,
    ]

    column_labels = {
        ProductHall.id: "웨딩홀 ID",
        "product.name": "상품명",
        "product.address": "주소",
        "product.description": "설명",
        "product.enterprise.name": "업체명",
        "product.available": "판매 여부",
        ProductHall.product_id: "상품 ID",
        ProductHall.hall_type: "홀 종류",
        ProductHall.hall_style: "홀 스타일",
        ProductHall.min_capacity: "최소 수용 인원",
        ProductHall.max_capacity: "최대 수용 인원",
        ProductHall.guaranteed_min_count: "보증 인원",
        ProductHall.wedding_type: "예식 진행 방식",
        ProductHall.wedding_running_time: "예식 진행 시간",
        ProductHall.food_type: "식사 타입",
        ProductHall.food_cost: "식사 비용",
        ProductHall.elevator: "엘리베이터 여부",
        ProductHall.valet_parking: "발렛 파킹 여부",
        ProductHall.pyebaek_room: "폐백실 여부",
        ProductHall.family_waiting_room: "혼주 대기실 여부",
        ProductHall.atm: "ATM 기기 여부",
        ProductHall.dress_room: "드레스룸 여부",
        ProductHall.smoking_area: "흡연실 여부",
        ProductHall.photo_zone: "포토존 여부",
        ProductHall.is_deleted: "삭제 여부",
        ProductHall.created_datetime: "생성일시",
        ProductHall.updated_datetime: "수정일시",
        ProductHall.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        ProductHall.id,
        ProductHall.product_id,
        "product.name",
        "product.description",
        "product.enterprise.name",
        "product.address",
        "product.available",
        ProductHall.hall_type,
        ProductHall.hall_style,
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.wedding_type,
        ProductHall.wedding_running_time,
        ProductHall.food_type,
        ProductHall.food_cost,
        ProductHall.elevator,
        ProductHall.valet_parking,
        ProductHall.pyebaek_room,
        ProductHall.family_waiting_room,
        ProductHall.atm,
        ProductHall.dress_room,
        ProductHall.smoking_area,
        ProductHall.photo_zone,
        ProductHall.is_deleted,
        ProductHall.created_datetime,
        ProductHall.updated_datetime,
        ProductHall.deleted_datetime,
    ]

    column_searchable_list = [
        "product.name",
        "product.address",
        ProductHall.hall_type,
        ProductHall.hall_style,
        ProductHall.food_type,
    ]

    column_sortable_list = [
        ProductHall.id,
        # "product.name" 정렬은 별도 구현 필요
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.guaranteed_min_count,
        ProductHall.food_cost,
        ProductHall.wedding_running_time,
        ProductHall.created_datetime,
        ProductHall.updated_datetime,
    ]

    column_formatters = {
        ProductHall.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductHall.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductHall.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True

    async def delete_model(self, request: Request, pk: Any) -> None:
        obj = await self.get_object_for_details(pk)
        obj.is_deleted = True
        # 연결된 Product도 삭제 처리할지 결정
        # obj.product.is_deleted = True
        await self.update_model(request, pk, obj.dict())
