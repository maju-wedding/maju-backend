from admin.models.base import BaseModelViewWithFilters
from models.magazines import Magazine


class MagazineAdmin(BaseModelViewWithFilters, model=Magazine):
    name = "매거진"
    name_plural = "매거진 목록"
    icon = "fa-solid fa-book-open"
    category = "콘텐츠 관리"

    # 목록 페이지에서 보여줄 컬럼들
    column_list = [
        Magazine.id,
        Magazine.title,
        Magazine.thumbnail_url,
        Magazine.content_image_urls,
        Magazine.created_datetime,
        Magazine.updated_datetime,
        Magazine.is_deleted,
    ]

    # 컬럼 라벨 설정
    column_labels = {
        Magazine.id: "ID",
        Magazine.title: "제목",
        Magazine.thumbnail_url: "썸네일",
        Magazine.content_image_urls: "콘텐츠 이미지 개수",
        Magazine.created_datetime: "생성일시",
        Magazine.updated_datetime: "수정일시",
        Magazine.is_deleted: "삭제 여부",
    }

    # 상세 페이지에서 보여줄 컬럼들
    column_details_list = [
        Magazine.id,
        Magazine.title,
        Magazine.thumbnail_url,
        Magazine.content_image_urls,
        Magazine.created_datetime,
        Magazine.updated_datetime,
        Magazine.is_deleted,
    ]

    # 생성/수정 폼에서 사용할 필드들
    form_columns = [
        Magazine.title,
        Magazine.thumbnail_url,
        Magazine.content_image_urls,
    ]

    # 검색 가능한 필드들
    column_searchable_list = [Magazine.title]

    # 필터링 가능한 필드들
    column_filters = [
        Magazine.created_datetime,
        Magazine.is_deleted,
    ]

    # 정렬 가능한 필드들
    column_sortable_list = [
        Magazine.id,
        Magazine.title,
        Magazine.created_datetime,
        Magazine.updated_datetime,
    ]

    column_formatters = {
        Magazine.thumbnail_url: lambda m, a: (
            f'<div class="flex items-center gap-2">'
            f'<img src="{m.thumbnail_url}" alt="썸네일" class="w-12 h-12 object-cover rounded" '
            f"onerror=\"this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMiA4VjE2TTE2IDEySDgiIHN0cm9rZT0iIzlDQTNBRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+Cg=='\">"
            f"</div>"
            if m.thumbnail_url
            else '<span class="text-gray-400">썸네일 없음</span>'
        ),
        Magazine.content_image_urls: lambda m, a: len(m.content_image_urls),
        Magazine.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        Magazine.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        Magazine.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    column_formatters_detail = {
        Magazine.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
        Magazine.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        Magazine.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }
