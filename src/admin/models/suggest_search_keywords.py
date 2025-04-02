from admin.models.base import BaseModelViewWithFilters
from models import SuggestSearchKeyword


class SuggestSearchKeywordAdmin(BaseModelViewWithFilters, model=SuggestSearchKeyword):
    name = "검색"
    name_plural = "추천검색어"
    icon = "fa-solid fa-building"
    category = "검색 관리"

    column_list = [
        SuggestSearchKeyword.id,
        SuggestSearchKeyword.keyword,
        SuggestSearchKeyword.is_deleted,
    ]

    column_labels = {
        SuggestSearchKeyword.id: "추천 검색어 ID",
        SuggestSearchKeyword.keyword: "검색어",
        SuggestSearchKeyword.is_deleted: "삭제 여부",
        SuggestSearchKeyword.created_datetime: "생성일시",
        SuggestSearchKeyword.updated_datetime: "수정일시",
        SuggestSearchKeyword.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        SuggestSearchKeyword.id,
        SuggestSearchKeyword.keyword,
        SuggestSearchKeyword.is_deleted,
        SuggestSearchKeyword.created_datetime,
        SuggestSearchKeyword.updated_datetime,
        SuggestSearchKeyword.deleted_datetime,
    ]

    form_excluded_columns = [
        SuggestSearchKeyword.is_deleted,
        SuggestSearchKeyword.created_datetime,
        SuggestSearchKeyword.updated_datetime,
        SuggestSearchKeyword.deleted_datetime,
    ]

    column_searchable_list = []

    column_sortable_list = []

    column_formatters_detail = {
        SuggestSearchKeyword.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        SuggestSearchKeyword.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        SuggestSearchKeyword.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
