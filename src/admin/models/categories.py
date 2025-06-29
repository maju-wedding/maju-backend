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
        Category.icon_url,
        Category.created_datetime,
        Category.updated_datetime,
        Category.is_deleted,
    ]

    column_labels = {
        Category.id: "카테고리 ID",
        Category.display_name: "표시 이름",
        Category.is_system_category: "기본 카테고리",
        Category.icon_url: "아이콘",
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
        Category.icon_url: lambda m, a: (
            f'<div class="flex items-center gap-2">'
            f'<img src="{m.icon_url}" alt="아이콘" class="w-6 h-6 object-cover rounded" '
            f"onerror=\"this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMiA4VjE2TTE2IDEySDgiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+Cg=='\">"
            f"</div>"
            if m.icon_url
            else '<span class="text-gray-400">이미지 없음</span>'
        ),
    }

    column_formatters_detail = {
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

    form_columns = [
        Category.display_name,
        Category.icon_url,
        Category.is_system_category,
    ]

    def list_query(self, request):
        query = super().list_query(request)

        is_system_category = request.query_params.get("is_system_category")
        if is_system_category == "true":
            query = query.where(self.model.is_system_category == True)
        elif is_system_category == "false":
            query = query.where(self.model.is_system_category == False)

        return query

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
