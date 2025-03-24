from typing import Any

from starlette.requests import Request

from admin.models.base import BaseModelViewWithFilters
from models import ProductAIReview


class ProductAIReviewAdmin(BaseModelViewWithFilters, model=ProductAIReview):
    name = "상품"
    name_plural = "AI 요약"
    icon = "fa-solid fa-building"
    category = "상품 관리"

    column_list = [
        ProductAIReview.id,
        "product.category.name",
        "product.name",
        ProductAIReview.review_type,
        ProductAIReview.content,
        ProductAIReview.is_deleted,
    ]

    column_labels = {
        ProductAIReview.id: "ID",
        "product.category.name": "카테고리",
        "product.name": "상품명",
        ProductAIReview.review_type: "리뷰 타입",
        ProductAIReview.content: "내용",
        ProductAIReview.is_deleted: "삭제 여부",
    }

    column_details_list = [
        ProductAIReview.id,
        "product.name",
        ProductAIReview.review_type,
        ProductAIReview.content,
        ProductAIReview.is_deleted,
        ProductAIReview.created_datetime,
        ProductAIReview.updated_datetime,
        ProductAIReview.deleted_datetime,
    ]

    column_searchable_list = [
        "product.name",
    ]

    column_sortable_list = [
        ProductAIReview.id,
        ProductAIReview.review_type,
    ]

    column_formatters_detail = {
        ProductAIReview.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductAIReview.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductAIReview.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    form_edit_rules = [
        "review_type",
        "content",
    ]

    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True

    async def delete_model(self, request: Request, pk: Any) -> None:
        obj = await self.get_object_for_details(pk)
        obj.is_deleted = True
        # 연결된 Product도 삭제 처리할지 결정
        # obj.product.is_deleted = True
        await self.update_model(request, pk, obj.dict())
