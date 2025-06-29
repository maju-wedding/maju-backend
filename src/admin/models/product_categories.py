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
    ]

    column_labels = {
        ProductCategory.id: "카테고리 ID",
        ProductCategory.name: "이름",
        ProductCategory.display_name: "표시 이름",
        ProductCategory.type: "유형",
        ProductCategory.is_ready: "준비 여부",
        ProductCategory.order: "순서",
        ProductCategory.icon_url: "아이콘 URL",
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
