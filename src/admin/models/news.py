from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from wtforms import SelectField
from wtforms.validators import DataRequired

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
        "news_items_count",  # 커스텀 필드
        NewsCategory.created_datetime,
        NewsCategory.updated_datetime,
    ]

    # 컬럼 라벨 설정
    column_labels = {
        NewsCategory.id: "ID",
        NewsCategory.display_name: "카테고리명",
        "news_items_count": "뉴스 개수",
        NewsCategory.created_datetime: "생성일시",
        NewsCategory.updated_datetime: "수정일시",
    }

    # 상세 페이지에서 보여줄 컬럼들
    column_details_list = [
        NewsCategory.id,
        NewsCategory.display_name,
        NewsCategory.created_datetime,
        NewsCategory.updated_datetime,
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

    # 기본 정렬
    column_default_sort = [(NewsCategory.created_datetime, True)]

    # 페이지당 아이템 수
    page_size = 20

    async def list_context(self, request: Request, objects: list) -> dict:
        """목록 페이지 컨텍스트 확장 - 뉴스 개수 추가"""
        context = await super().list_context(request, objects)

        # 각 카테고리의 뉴스 개수 계산
        session = request.state.session
        enhanced_objects = []

        for obj in objects:
            # 해당 카테고리의 뉴스 개수 조회
            count_query = select(func.count(NewsItem.id)).where(
                NewsItem.news_category_id == obj.id, NewsItem.is_deleted == False
            )
            result = await session.execute(count_query)
            news_count = result.scalar() or 0

            obj_dict = obj.__dict__.copy()
            obj_dict["news_items_count"] = news_count
            enhanced_objects.append(obj_dict)

        context["objects"] = enhanced_objects
        return context


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
        NewsItem.news_category_id: "카테고리",
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
        NewsItem.news_category_id,
        NewsItem.link_url,
        NewsItem.post_date,
    ]

    form_overrides = {"news_category_id": SelectField}

    # 폼 필드 설정
    form_args = {
        "news_category_id": {
            "label": "카테고리",
            "validators": [DataRequired("카테고리를 선택해주세요.")],
            "coerce": int,
        },
        "title": {
            "label": "제목",
            "validators": [DataRequired("제목을 입력해주세요.")],
        },
        "link_url": {
            "label": "링크 URL",
            "validators": [DataRequired("링크 URL을 입력해주세요.")],
        },
        "post_date": {
            "label": "게시일",
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

    # 기본 정렬
    column_default_sort = [(NewsItem.post_date, True)]  # 최신 게시일순

    # 페이지당 아이템 수
    page_size = 20

    def list_query(self, request: Request) -> Any:
        """목록 쿼리 커스터마이징 - 카테고리 정보 포함"""
        query = (
            select(self.model)
            .options(selectinload(self.model.news_category))
            .where(self.model.is_deleted == False)
        )

        # 카테고리 필터링
        category_id = request.query_params.get("category_id")
        if category_id:
            try:
                query = query.where(self.model.news_category_id == int(category_id))
            except (ValueError, TypeError):
                pass

        # 페이징 처리
        page = int(request.query_params.get("page", 1))
        offset = (page - 1) * self.page_size
        query = query.offset(offset).limit(self.page_size)

        return query

    async def scaffold_form(self, rules=None):
        """폼 생성 시 카테고리 선택지 동적 설정"""
        form_class = await super().scaffold_form(rules)

        # 카테고리 필드의 choices를 동적으로 설정하는 함수
        async def set_category_choices(form_instance, request):
            session = request.state.session
            categories_query = (
                select(NewsCategory)
                .where(NewsCategory.is_deleted == False)
                .order_by(NewsCategory.display_name)
            )
            result = await session.execute(categories_query)
            categories = result.scalars().all()

            if hasattr(form_instance, "news_category_id"):
                form_instance.news_category_id.choices = [
                    (category.id, category.display_name) for category in categories
                ]

            return form_instance

        # 폼 클래스에 choices 설정 함수 추가
        form_class._set_category_choices = set_category_choices
        return form_class

    async def create_form(self, request: Request):
        """생성 폼에서 카테고리 선택지 설정"""
        form = await super().create_form(request)

        # 카테고리 목록 가져오기
        session = request.state.session
        categories_query = (
            select(NewsCategory)
            .where(NewsCategory.is_deleted == False)
            .order_by(NewsCategory.display_name)
        )
        result = await session.execute(categories_query)
        categories = result.scalars().all()

        # 선택지 설정
        if hasattr(form, "news_category_id"):
            form.news_category_id.choices = [
                (category.id, category.display_name) for category in categories
            ]

        return form

    async def edit_form(self, request: Request, obj: NewsItem):
        """수정 폼에서 카테고리 선택지 설정"""
        form = await super().edit_form(request, obj)

        # 카테고리 목록 가져오기
        session = request.state.session
        categories_query = (
            select(NewsCategory)
            .where(NewsCategory.is_deleted == False)
            .order_by(NewsCategory.display_name)
        )
        result = await session.execute(categories_query)
        categories = result.scalars().all()

        # 선택지 설정
        if hasattr(form, "news_category_id"):
            form.news_category_id.choices = [
                (category.id, category.display_name) for category in categories
            ]
            # 현재 값 설정
            form.news_category_id.data = obj.news_category_id

        return form
