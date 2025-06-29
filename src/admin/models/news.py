from admin.models.base import BaseModelViewWithFilters
from models import NewsCategory, NewsItem


class NewsCategoryAdmin(BaseModelViewWithFilters, model=NewsCategory):
    name = "뉴스 카테고리"
    name_plural = "뉴스 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "콘텐츠 관리"

    # 목록 페이지에서 보여줄 컬럼들
    column_list = [
        NewsCategory.id,
        NewsCategory.display_name,
        NewsCategory.news_items,
        NewsCategory.created_datetime,
        NewsCategory.updated_datetime,
        NewsCategory.is_deleted,
    ]

    # 컬럼 라벨 설정
    column_labels = {
        NewsCategory.id: "ID",
        NewsCategory.display_name: "카테고리명",
        NewsCategory.news_items: "뉴스 개수",
        NewsCategory.created_datetime: "생성일시",
        NewsCategory.updated_datetime: "수정일시",
        NewsCategory.is_deleted: "삭제 여부",
    }

    # 상세 페이지에서 보여줄 컬럼들
    column_details_list = [
        NewsCategory.id,
        NewsCategory.display_name,
        NewsCategory.created_datetime,
        NewsCategory.updated_datetime,
        NewsCategory.is_deleted,
    ]

    # 생성/수정 폼에서 사용할 필드들
    form_columns = [
        NewsCategory.display_name,
    ]

    # 검색 가능한 필드들
    column_searchable_list = [NewsCategory.display_name]

    # 필터링 가능한 필드들
    column_filters = [
        NewsCategory.created_datetime,
    ]

    # 정렬 가능한 필드들
    column_sortable_list = [
        NewsCategory.id,
        NewsCategory.display_name,
        NewsCategory.created_datetime,
    ]

    column_formatters = {
        NewsCategory.news_items: lambda m, a: len(m.news_items),
        NewsCategory.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        NewsCategory.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        NewsCategory.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    column_formatters_detail = {
        NewsCategory.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        NewsCategory.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        NewsCategory.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }


class NewsItemAdmin(BaseModelViewWithFilters, model=NewsItem):
    name = "뉴스"
    name_plural = "뉴스 목록"
    icon = "fa-solid fa-newspaper"
    category = "콘텐츠 관리"

    # 목록 페이지에서 보여줄 컬럼들
    column_list = [
        NewsItem.id,
        NewsItem.title,
        "news_category.display_name",  # 관계 필드
        NewsItem.link_url,
        NewsItem.post_date,
        NewsItem.created_datetime,
        NewsItem.is_deleted,
    ]

    # 컬럼 라벨 설정
    column_labels = {
        NewsItem.id: "ID",
        NewsItem.title: "제목",
        NewsItem.news_category: "카테고리",
        "news_category.display_name": "카테고리",
        NewsItem.link_url: "링크 URL",
        NewsItem.post_date: "게시일",
        NewsItem.created_datetime: "생성일시",
        NewsItem.updated_datetime: "수정일시",
        NewsItem.is_deleted: "삭제 여부",
    }

    # 상세 페이지에서 보여줄 컬럼들
    column_details_list = [
        NewsItem.id,
        NewsItem.title,
        NewsItem.news_category_id,
        NewsItem.link_url,
        NewsItem.post_date,
        NewsItem.created_datetime,
        NewsItem.updated_datetime,
        NewsItem.is_deleted,
    ]

    # 생성/수정 폼에서 사용할 필드들
    form_columns = [
        NewsItem.title,
        NewsItem.news_category,
        NewsItem.link_url,
        NewsItem.post_date,
    ]

    form_ajax_refs = {
        "news_category": {
            "fields": (
                "id",
                "display_name",
            ),
            "order_by": "id",
        },
    }

    # 검색 가능한 필드들
    column_searchable_list = [
        NewsItem.title,
        NewsItem.link_url,
    ]

    # 필터링 가능한 필드들
    column_filters = [
        NewsItem.news_category_id,
        NewsItem.post_date,
        NewsItem.created_datetime,
        NewsItem.is_deleted,
    ]

    # 정렬 가능한 필드들
    column_sortable_list = [
        NewsItem.id,
        NewsItem.title,
        NewsItem.post_date,
        NewsItem.created_datetime,
    ]

    column_formatters = {
        NewsCategory.news_items: lambda m, a: len(m.news_items),
        NewsItem.link_url: lambda m, a: (
            f'<a href="{m.link_url}" target="_blank" class="text-blue-600 hover:text-blue-800 underline">'
            f'{m.link_url[:50]}{"..." if len(m.link_url) > 50 else ""}</a>'
            if m.link_url
            else "-"
        ),
        NewsItem.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        NewsItem.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        NewsItem.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    column_formatters_detail = {
        NewsItem.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        NewsItem.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        NewsItem.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
