from typing import Any

from starlette.requests import Request

from admin.models.base import BaseModelViewWithFilters
from models.product_hall_venues import ProductHallVenue


class ProductHallVenueAdmin(BaseModelViewWithFilters, model=ProductHallVenue):
    name = "홀"
    name_plural = "홀 목록"
    icon = "fa-solid fa-building"
    category = "상품 관리"

    column_list = [
        ProductHallVenue.id,
        "product_hall.name",
        ProductHallVenue.name,
        "thumbnail",
        "images",
        ProductHallVenue.wedding_interval,
        ProductHallVenue.wedding_times,
        ProductHallVenue.wedding_type,
        ProductHallVenue.hall_styles,
        ProductHallVenue.hall_types,
        ProductHallVenue.guaranteed_min_count,
        ProductHallVenue.min_capacity,
        ProductHallVenue.max_capacity,
        ProductHallVenue.basic_price,
        ProductHallVenue.peak_season_price,
        ProductHallVenue.ceiling_height,
        ProductHallVenue.virgin_road_length,
        ProductHallVenue.include_drink,
        ProductHallVenue.include_alcohol,
        ProductHallVenue.include_service_fee,
        ProductHallVenue.include_vat,
        ProductHallVenue.bride_room_entry_methods,
        ProductHallVenue.bride_room_makeup_room,
        ProductHallVenue.food_menu,
        ProductHallVenue.food_cost_per_adult,
        ProductHallVenue.food_cost_per_child,
        ProductHallVenue.banquet_hall_running_time,
        ProductHallVenue.banquet_hall_max_capacity,
        ProductHallVenue.has_bride_room,
        ProductHallVenue.has_pyebaek_room,
        ProductHallVenue.has_banquet_hall,
        ProductHallVenue.has_stage,
        ProductHallVenue.additional_info,
        ProductHallVenue.special_notes,
    ]

    column_labels = {
        ProductHallVenue.id: "홀 ID",
        "product_hall.name": "웨딩홀명",
        "thumbnail": "썸네일",
        "images": "이미지 개수",
        ProductHallVenue.hall_styles: "홀 스타일",
        ProductHallVenue.hall_types: "홀 타입",
        ProductHallVenue.name: "홀 이름",
        ProductHallVenue.wedding_interval: "예식 간격",
        ProductHallVenue.wedding_times: "예식 시간",
        ProductHallVenue.wedding_type: "예식 타입",
        ProductHallVenue.guaranteed_min_count: "보증 인원",
        ProductHallVenue.min_capacity: "최소 수용인원",
        ProductHallVenue.max_capacity: "최대 수용인원",
        ProductHallVenue.basic_price: "비수기 가격",
        ProductHallVenue.peak_season_price: "성수기 가격",
        ProductHallVenue.ceiling_height: "천장 높이",
        ProductHallVenue.virgin_road_length: "버진로드 길이",
        ProductHallVenue.include_drink: "음료 포함",
        ProductHallVenue.include_alcohol: "주류 포함",
        ProductHallVenue.include_service_fee: "서비스료 포함",
        ProductHallVenue.include_vat: "부가세 포함",
        ProductHallVenue.bride_room_entry_methods: "신부 입장 방법",
        ProductHallVenue.bride_room_makeup_room: "신부 화장실 여부",
        ProductHallVenue.food_menu: "식사 종류",
        ProductHallVenue.food_cost_per_adult: "성인 음식 가격",
        ProductHallVenue.food_cost_per_child: "아동 음식 가격",
        ProductHallVenue.banquet_hall_running_time: "연회장 이용 시간",
        ProductHallVenue.banquet_hall_max_capacity: "연회장 최대 수용인원",
        ProductHallVenue.has_bride_room: "신부대기실 여부",
        ProductHallVenue.has_pyebaek_room: "폐백실 여부",
        ProductHallVenue.has_banquet_hall: "연회장 여부",
        ProductHallVenue.has_stage: "단상 여부",
        ProductHallVenue.additional_info: "추가 정보",
        ProductHallVenue.special_notes: "특이 사항",
        ProductHallVenue.is_deleted: "삭제 여부",
        ProductHallVenue.created_datetime: "생성일시",
        ProductHallVenue.updated_datetime: "수정일시",
        ProductHallVenue.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        ProductHallVenue.id,
        "product_hall.name",
        ProductHallVenue.name,
        ProductHallVenue.wedding_interval,
        ProductHallVenue.wedding_times,
        ProductHallVenue.wedding_type,
        ProductHallVenue.guaranteed_min_count,
        ProductHallVenue.min_capacity,
        ProductHallVenue.max_capacity,
        ProductHallVenue.basic_price,
        ProductHallVenue.peak_season_price,
        ProductHallVenue.ceiling_height,
        ProductHallVenue.virgin_road_length,
        ProductHallVenue.include_drink,
        ProductHallVenue.include_alcohol,
        ProductHallVenue.include_service_fee,
        ProductHallVenue.include_vat,
        ProductHallVenue.bride_room_entry_methods,
        ProductHallVenue.bride_room_makeup_room,
        "food_type.name",
        ProductHallVenue.food_cost_per_adult,
        ProductHallVenue.food_cost_per_child,
        ProductHallVenue.banquet_hall_running_time,
        ProductHallVenue.banquet_hall_max_capacity,
        ProductHallVenue.additional_info,
        ProductHallVenue.special_notes,
        ProductHallVenue.is_deleted,
        ProductHallVenue.created_datetime,
        ProductHallVenue.updated_datetime,
        ProductHallVenue.deleted_datetime,
    ]

    column_searchable_list = [
        ProductHallVenue.name,
        "product_hall.name",
    ]

    column_sortable_list = [
        ProductHallVenue.id,
        "product_hall.name",
        ProductHallVenue.name,
        ProductHallVenue.wedding_type,
    ]

    column_formatters = {
        ProductHallVenue.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductHallVenue.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductHallVenue.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
        "thumbnail": lambda m, a: (
            f'<img src="{m.images[0].image_url}" alt="홀 이미지" class="w-12 h-12 object-cover rounded border" '
            f"onerror=\"this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMiA4VjE2TTE2IDEySDgiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+Cg=='\">"
            if m.images and len(m.images) > 0
            else '<div class="w-12 h-12 bg-gray-100 rounded border flex items-center justify-center"><i class="fas fa-image text-gray-300"></i></div>'
        ),
        "images": lambda m, a: len(m.images),
    }

    column_formatters_detail = {
        ProductHallVenue.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductHallVenue.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductHallVenue.deleted_datetime: lambda m, a: (
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
