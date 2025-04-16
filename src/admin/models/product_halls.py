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
        ProductHall.name,
        "product.address",
        "product.sido",
        "product.gugun",
        "product.ai_reviews",
        "product.park_limit",
        "product.park_free_hours",
        "product.subway_line",
        "product.subway_name",
        "product.subway_exit",
        ProductHall.elevator_count,
        ProductHall.atm_count,
        ProductHall.has_pyebaek_room,
        ProductHall.has_family_waiting_room,
        # ProductHall.valet_parking,
        # ProductHall.dress_room,
        # ProductHall.smoking_area,
        # ProductHall.photo_zone,
        ProductHall.is_deleted,
    ]

    column_labels = {
        ProductHall.id: "웨딩홀 ID",
        ProductHall.name: "웨딩홀명",
        "product.address": "주소",
        "product.sido": "시도",
        "product.gugun": "구군",
        "product.ai_reviews": "AI 요약",
        "product.park_limit": "주차 가능 대수",
        "product.park_free_hours": "주차 무료 시간",
        "product.subway_line": "지하철 호선",
        "product.subway_name": "지하철 역",
        "product.subway_exit": "지하철 출구",
        "product.description": "설명",
        "product.enterprise.name": "업체명",
        "product.available": "판매 여부",
        "product.tel": "전화번호",
        "product.fax_tel": "팩스번호",
        "product.way_text": "오시는 길",
        "product.holiday": "휴무일",
        "product.business_hours": "영업시간",
        ProductHall.product_id: "상품 ID",
        ProductHall.elevator_count: "엘리베이터 개수",
        ProductHall.has_pyebaek_room: "폐백실 여부",
        ProductHall.has_family_waiting_room: "혼주 대기실 여부",
        ProductHall.atm_count: "ATM 기기 여부",
        # ProductHall.valet_parking: "발렛 파킹 여부",
        # ProductHall.dress_room: "드레스룸 여부",
        # ProductHall.smoking_area: "흡연실 여부",
        # ProductHall.photo_zone: "포토존 여부",
        ProductHall.is_deleted: "삭제 여부",
        ProductHall.created_datetime: "생성일시",
        ProductHall.updated_datetime: "수정일시",
        ProductHall.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        ProductHall.id,
        ProductHall.product_id,
        "product.description",
        "product.address",
        "product.sido",
        "product.gugun",
        "product.park_limit",
        "product.park_free_hours",
        "product.subway_line",
        "product.subway_name",
        "product.subway_exit",
        "product.tel",
        "product.fax_tel",
        "product.way_text",
        "product.holiday",
        "product.business_hours",
        "product.enterprise.name",
        "product.available",
        ProductHall.elevator_count,
        ProductHall.atm_count,
        ProductHall.has_pyebaek_room,
        ProductHall.has_family_waiting_room,
        # ProductHall.valet_parking,
        # ProductHall.dress_room,
        # ProductHall.smoking_area,
        # ProductHall.photo_zone,
        ProductHall.is_deleted,
        ProductHall.created_datetime,
        ProductHall.updated_datetime,
        ProductHall.deleted_datetime,
    ]

    column_searchable_list = [
        "product.name",
        "product.address",
    ]

    column_sortable_list = [
        ProductHall.id,
        "product.sido",
        "product.gugun",
    ]

    column_formatters = {
        "product.ai_reviews": lambda m, a: [
            ai_review.review_type for ai_review in m.product.ai_reviews
        ],
    }

    column_formatters_detail = {
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
