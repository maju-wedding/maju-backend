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
        "category.display_name",
        Checklist.user_id,
        Checklist.is_completed,
        Checklist.is_system_checklist,
        Checklist.global_display_order,
        Checklist.created_datetime,
        Checklist.updated_datetime,
        Checklist.is_deleted,
    ]

    column_labels = {
        Checklist.id: "체크리스트 ID",
        Checklist.title: "제목",
        Checklist.description: "설명",
        "category.display_name": "체크리스트 카테고리",
        Checklist.category_id: "카테고리",
        Checklist.is_system_checklist: "기본 체크리스트",
        Checklist.user_id: "사용자 ID",
        Checklist.is_completed: "완료 여부",
        Checklist.completed_datetime: "완료일시",
        Checklist.global_display_order: "전체 표시 순서",
        Checklist.is_deleted: "삭제 여부",
        Checklist.created_datetime: "생성일시",
        Checklist.updated_datetime: "수정일시",
        Checklist.deleted_datetime: "삭제일시",
        Checklist.category: "카테고리",
        Checklist.user: "유저",
    }

    # form_columns 대신 form_excluded_columns만 사용
    form_excluded_columns = [
        Checklist.is_deleted,
        Checklist.created_datetime,
        Checklist.updated_datetime,
        Checklist.deleted_datetime,
        Checklist.completed_datetime,
        Checklist.global_display_order,
        Checklist.category_display_order,
    ]

    # AJAX를 사용한 외래키 참조
    form_ajax_refs = {
        "category": {
            "fields": (
                "id",
                "display_name",
            ),
            "order_by": "id",
        },
        "user": {
            "fields": ("id", "email", "nickname"),
            "order_by": "id",
        },
    }

    column_searchable_list = [
        Checklist.title,
        Checklist.description,
    ]

    column_sortable_list = [
        Checklist.id,
        Checklist.title,
        Checklist.category_id,
        Checklist.global_display_order,
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

    column_formatters_detail = {
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

    def list_query(self, request):
        query = super().list_query(request)

        is_system_checklist = request.query_params.get("is_system_checklist")
        if is_system_checklist == "true":
            query = query.where(self.model.is_system_checklist == True)
        elif is_system_checklist == "false":
            query = query.where(self.model.is_system_checklist == False)

        is_completed = request.query_params.get("is_completed")
        if is_completed == "true":
            query = query.where(self.model.is_completed == True)
        elif is_completed == "false":
            query = query.where(self.model.is_completed == False)

        return query

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
