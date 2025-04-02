from admin.models.base import BaseModelViewWithFilters
from models import ChecklistCategory


class ChecklistCategoryAdmin(BaseModelViewWithFilters, model=ChecklistCategory):
    name = "체크리스트 카테고리"
    name_plural = "체크리스트 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "체크리스트 관리"

    column_list = [
        ChecklistCategory.id,
        ChecklistCategory.display_name,
        ChecklistCategory.is_system_category,
        # ChecklistCategory.user_id,
        # ChecklistCategory.created_datetime,
        ChecklistCategory.is_deleted,
    ]

    column_labels = {
        ChecklistCategory.id: "카테고리 ID",
        ChecklistCategory.display_name: "표시 이름",
        ChecklistCategory.is_system_category: "기본 카테고리",
        # ChecklistCategory.user_id: "사용자 ID",
        ChecklistCategory.created_datetime: "생성일시",
        ChecklistCategory.updated_datetime: "수정일시",
        ChecklistCategory.deleted_datetime: "삭제일시",
        ChecklistCategory.is_deleted: "삭제 여부",
    }

    column_details_list = [
        ChecklistCategory.id,
        ChecklistCategory.display_name,
        ChecklistCategory.is_system_category,
        ChecklistCategory.user_id,
        ChecklistCategory.is_deleted,
        ChecklistCategory.created_datetime,
        ChecklistCategory.updated_datetime,
        ChecklistCategory.deleted_datetime,
    ]

    column_searchable_list = [
        ChecklistCategory.display_name,
    ]

    column_sortable_list = [
        ChecklistCategory.id,
        ChecklistCategory.display_name,
        ChecklistCategory.created_datetime,
        ChecklistCategory.updated_datetime,
    ]

    column_formatters = {
        ChecklistCategory.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        ChecklistCategory.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        ChecklistCategory.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    form_excluded_columns = [
        ChecklistCategory.is_deleted,
        ChecklistCategory.created_datetime,
        ChecklistCategory.updated_datetime,
        ChecklistCategory.deleted_datetime,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
