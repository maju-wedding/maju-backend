from admin.models.base import BaseModelViewWithFilters
from models import Category


class CategoryAdmin(BaseModelViewWithFilters, model=Category):
    name = "체크리스트 카테고리"
    name_plural = "체크리스트 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "체크리스트 관리"

    column_list = [
        Category.id,
        Category.display_name,
        Category.is_system_category,
        # Category.user_id,
        # Category.created_datetime,
        Category.is_deleted,
    ]

    column_labels = {
        Category.id: "카테고리 ID",
        Category.display_name: "표시 이름",
        Category.is_system_category: "기본 카테고리",
        # Category.user_id: "사용자 ID",
        Category.created_datetime: "생성일시",
        Category.updated_datetime: "수정일시",
        Category.deleted_datetime: "삭제일시",
        Category.is_deleted: "삭제 여부",
    }

    column_details_list = [
        Category.id,
        Category.display_name,
        Category.is_system_category,
        Category.user_id,
        Category.is_deleted,
        Category.created_datetime,
        Category.updated_datetime,
        Category.deleted_datetime,
    ]

    column_searchable_list = [
        Category.display_name,
    ]

    column_sortable_list = [
        Category.id,
        Category.display_name,
        Category.created_datetime,
        Category.updated_datetime,
    ]

    column_formatters = {
        Category.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        Category.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        Category.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    form_excluded_columns = [
        Category.is_deleted,
        Category.created_datetime,
        Category.updated_datetime,
        Category.deleted_datetime,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
