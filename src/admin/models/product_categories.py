from admin.models.base import BaseModelViewWithFilters
from models import ProductCategory


class ProductCategoryAdmin(BaseModelViewWithFilters, model=ProductCategory):
    name = "상품 카테고리"
    name_plural = "상품 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "상품 관리"

    column_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
        ProductCategory.icon_url,
        ProductCategory.created_datetime,
        ProductCategory.updated_datetime,
    ]

    column_labels = {
        ProductCategory.id: "카테고리 ID",
        ProductCategory.name: "이름",
        ProductCategory.display_name: "표시 이름",
        ProductCategory.type: "유형",
        ProductCategory.is_ready: "준비 여부",
        ProductCategory.order: "순서",
        ProductCategory.icon_url: "아이콘",
        ProductCategory.created_datetime: "생성일시",
        ProductCategory.updated_datetime: "수정일시",
    }

    column_details_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
    ]

    column_searchable_list = [
        ProductCategory.name,
        ProductCategory.display_name,
    ]

    column_sortable_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
    ]

    column_formatters = {
        ProductCategory.is_ready: lambda m, a: "O" if m.is_ready else "X",
        ProductCategory.icon_url: lambda m, a: (
            f'<div class="flex items-center gap-2">'
            f'<img src="{m.icon_url}" alt="아이콘" class="w-6 h-6 object-cover rounded" '
            f"onerror=\"this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMiA4VjE2TTE2IDEySDgiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+Cg=='\">"
            f"</div>"
            if m.icon_url
            else '<span class="text-gray-400">이미지 없음</span>'
        ),
        ProductCategory.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductCategory.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductCategory.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    column_formatters_detail = {
        ProductCategory.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ProductCategory.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ProductCategory.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    form_excluded_columns = [
        "products",
        ProductCategory.is_deleted,
        ProductCategory.created_datetime,
        ProductCategory.updated_datetime,
        ProductCategory.deleted_datetime,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
