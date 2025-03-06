from admin.models.base import BaseModelViewWithFilters
from models import Checklist


class ChecklistAdmin(BaseModelViewWithFilters, model=Checklist):
    name = "체크리스트"
    name_plural = "체크리스트 목록"
    icon = "fa-solid fa-check-square"
    category = "체크리스트 관리"

    column_list = [
        Checklist.id,
        Checklist.title,
        Checklist.checklist_category_id,
        Checklist.user_id,
        Checklist.is_completed,
        Checklist.is_system_checklist,
        Checklist.display_order,
        Checklist.is_deleted,
    ]

    column_labels = {
        Checklist.id: "체크리스트 ID",
        Checklist.title: "제목",
        Checklist.description: "설명",
        Checklist.checklist_category_id: "카테고리 ID",
        Checklist.is_system_checklist: "시스템 체크리스트 여부",
        Checklist.user_id: "사용자 ID",
        Checklist.is_completed: "완료 여부",
        Checklist.completed_datetime: "완료일시",
        Checklist.display_order: "표시 순서",
        Checklist.is_deleted: "삭제 여부",
        Checklist.created_datetime: "생성일시",
        Checklist.updated_datetime: "수정일시",
        Checklist.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        Checklist.id,
        Checklist.title,
        Checklist.description,
        Checklist.checklist_category_id,
        Checklist.is_system_checklist,
        Checklist.user_id,
        Checklist.is_completed,
        Checklist.completed_datetime,
        Checklist.display_order,
        Checklist.is_deleted,
        Checklist.created_datetime,
        Checklist.updated_datetime,
        Checklist.deleted_datetime,
    ]

    column_searchable_list = [
        Checklist.title,
        Checklist.description,
    ]

    column_sortable_list = [
        Checklist.id,
        Checklist.title,
        Checklist.checklist_category_id,
        Checklist.display_order,
        Checklist.created_datetime,
        Checklist.updated_datetime,
        Checklist.is_completed,
    ]

    column_formatters = {
        Checklist.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        Checklist.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        Checklist.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
        Checklist.completed_datetime: lambda m, a: (
            m.completed_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.completed_datetime
            else ""
        ),
    }

    form_excluded_columns = [
        Checklist.created_datetime,
        Checklist.updated_datetime,
        Checklist.deleted_datetime,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
