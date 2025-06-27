from typing import Any

from sqlalchemy import select
from starlette.requests import Request

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
        Magazine.thumbnail_url: "썸네일 URL",
        Magazine.content_image_urls: "콘텐츠 이미지",
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

    # 기본 정렬
    column_default_sort = [(Magazine.created_datetime, True)]  # 최신순

    # 페이지당 아이템 수
    page_size = 20

    def list_query(self, request: Request) -> Any:
        """목록 쿼리 커스터마이징"""
        query = select(self.model).where(self.model.is_deleted == False)

        # 페이징 처리
        page = int(request.query_params.get("page", 1))
        offset = (page - 1) * self.page_size
        query = query.offset(offset).limit(self.page_size)

        return query
