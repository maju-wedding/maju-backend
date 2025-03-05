from typing import Any

from sqladmin import ModelView
from sqlmodel import select
from starlette.requests import Request

from core.security import get_password_hash
from models import User, UserWishlist, Checklist, ProductCategory, ProductHall
from models.checklist_categories import ChecklistCategory


class BaseModelViewWithFilters(ModelView):
    """필터링 기능이 추가된 기본 ModelView 클래스"""

    # 커스텀 템플릿 지정
    # list_template = "custom/custom_list.html"  # 위에서 만든 템플릿 경로

    def list_query(self, request):
        """URL 쿼리 파라미터에서 필터 조건을 가져와 적용"""
        query = select(self.model)

        # 삭제 상태 필터
        is_deleted_param = request.query_params.get("is_deleted")
        if is_deleted_param == "true":
            query = query.where(self.model.is_deleted == True)
        elif is_deleted_param == "false":
            query = query.where(self.model.is_deleted == False)
        # is_deleted_param이
        # - None이면: 처음 페이지 접속 시 (기본적으로 삭제되지 않은 항목만 표시)
        # - 빈 문자열이면: "모두 보기" 옵션 선택 시
        elif is_deleted_param is None:
            query = query.where(self.model.is_deleted == False)

        return query


class UserAdmin(BaseModelViewWithFilters, model=User):
    name = "유저"
    name_plural = "유저 목록"
    icon = "fa-solid fa-users"
    category = "유저 관리"

    column_list = [
        User.id,
        User.email,
        User.nickname,
        User.phone_number,
        User.user_type,
        User.is_active,
        User.is_superuser,
        User.is_deleted,
    ]

    column_labels = {
        User.id: "사용자 ID",
        User.email: "이메일",
        User.nickname: "닉네임",
        User.hashed_password: "비밀번호",
        User.phone_number: "전화번호",
        User.user_type: "사용자 유형",
        User.is_active: "활성 여부",
        User.is_superuser: "관리자 여부",
        User.social_provider: "소셜 제공자",
        User.is_deleted: "삭제 여부",
        User.joined_datetime: "가입일시",
        User.updated_datetime: "수정일시",
        User.deleted_datetime: "삭제일시",
        User.service_policy_agreement: "서비스 정책 동의",
        User.privacy_policy_agreement: "개인정보 정책 동의",
        User.third_party_information_agreement: "제3자 정보 제공 동의",
    }

    column_details_list = [
        User.id,
        User.email,
        User.nickname,
        User.phone_number,
        User.user_type,
        User.social_provider,
        User.is_active,
        User.is_superuser,
        User.is_deleted,
        User.joined_datetime,
        User.updated_datetime,
        User.deleted_datetime,
        User.service_policy_agreement,
        User.privacy_policy_agreement,
        User.third_party_information_agreement,
    ]

    column_searchable_list = [
        User.email,
        User.nickname,
        User.phone_number,
    ]

    column_sortable_list = [
        User.id,
        User.email,
        User.nickname,
        User.joined_datetime,
        User.updated_datetime,
    ]

    column_formatters = {
        User.joined_datetime: lambda m, a: m.joined_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.joined_datetime
        else "",
        User.updated_datetime: lambda m, a: m.updated_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.updated_datetime
        else "",
        User.deleted_datetime: lambda m, a: m.deleted_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.deleted_datetime
        else "",
    }

    form_excluded_columns = [
        User.joined_datetime,
        User.updated_datetime,
        User.deleted_datetime,
    ]

    form_edit_rules = [
        "nickname",
        "phone_number",
        "user_type",
        "is_active",
        "is_superuser",
        "service_policy_agreement",
        "privacy_policy_agreement",
        "third_party_information_agreement",
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    def list_query(self, request):
        """User 모델에 특화된 필터링"""
        query = super().list_query(request)

        # 활성 상태 필터
        is_active_param = request.query_params.get("is_active")
        if is_active_param == "true":
            query = query.where(self.model.is_active == True)
        elif is_active_param == "false":
            query = query.where(self.model.is_active == False)

        # 사용자 유형 필터
        user_type_param = request.query_params.get("user_type")
        if user_type_param:
            query = query.where(self.model.user_type == user_type_param)

        return query

    async def insert_model(self, request: Request, data: dict) -> Any:
        if _password := data.get("hashed_password"):
            data["hashed_password"] = get_password_hash(_password)
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk: str, data: dict) -> Any:
        if _password := data.get("hashed_password"):
            obj = await self.get_object_for_details(pk)
            if _password != obj.hashed_password:
                data["hashed_password"] = get_password_hash(_password)
        return await super().update_model(request, pk, data)

    async def delete_model(self, request: Request, pk: Any) -> None:
        obj = await self.get_object_for_details(pk)
        obj.is_deleted = True
        await self.update_model(request, pk, obj.dict())


class UserWishlistAdmin(ModelView, model=UserWishlist):
    name = "위시리스트"
    name_plural = "위시리스트 목록"
    icon = "fa-solid fa-heart"
    category = "유저 관리"

    column_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    column_labels = {
        UserWishlist.id: "위시리스트 ID",
        UserWishlist.user_id: "사용자 ID",
        UserWishlist.product_id: "상품 ID",
        UserWishlist.created_datetime: "생성일시",
    }

    column_details_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    column_formatters = {
        UserWishlist.created_datetime: lambda m, a: m.created_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.created_datetime
        else "",
    }

    column_sortable_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    can_create = True
    can_edit = False  # Wishlists are typically not edited
    can_delete = True
    can_view_details = True


class ChecklistCategoryAdmin(BaseModelViewWithFilters, model=ChecklistCategory):
    name = "체크리스트 카테고리"
    name_plural = "체크리스트 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "체크리스트 관리"

    column_list = [
        ChecklistCategory.id,
        ChecklistCategory.display_name,
        ChecklistCategory.is_system_category,
        ChecklistCategory.user_id,
        ChecklistCategory.created_datetime,
        ChecklistCategory.is_deleted,
    ]

    column_labels = {
        ChecklistCategory.id: "카테고리 ID",
        ChecklistCategory.display_name: "표시 이름",
        ChecklistCategory.is_system_category: "시스템 카테고리 여부",
        ChecklistCategory.user_id: "사용자 ID",
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
        ChecklistCategory.created_datetime: lambda m, a: m.created_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.created_datetime
        else "",
        ChecklistCategory.updated_datetime: lambda m, a: m.updated_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.updated_datetime
        else "",
        ChecklistCategory.deleted_datetime: lambda m, a: m.deleted_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.deleted_datetime
        else "",
    }

    form_excluded_columns = [
        ChecklistCategory.created_datetime,
        ChecklistCategory.updated_datetime,
        ChecklistCategory.deleted_datetime,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


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
        Checklist.created_datetime: lambda m, a: m.created_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.created_datetime
        else "",
        Checklist.updated_datetime: lambda m, a: m.updated_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.updated_datetime
        else "",
        Checklist.deleted_datetime: lambda m, a: m.deleted_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.deleted_datetime
        else "",
        Checklist.completed_datetime: lambda m, a: m.completed_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.completed_datetime
        else "",
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


class ProductCategoryAdmin(BaseModelViewWithFilters, model=ProductCategory):
    name = "상품 카테고리"
    name_plural = "상품 카테고리 목록"
    icon = "fa-solid fa-folder"
    category = "상품 관리"

    column_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
    ]

    column_labels = {
        ProductCategory.id: "카테고리 ID",
        ProductCategory.name: "이름",
        ProductCategory.display_name: "표시 이름",
        ProductCategory.type: "유형",
        ProductCategory.is_ready: "준비 여부",
        ProductCategory.order: "순서",
    }

    column_details_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
    ]

    column_searchable_list = [
        ProductCategory.name,
        ProductCategory.display_name,
    ]

    column_sortable_list = [
        ProductCategory.id,
        ProductCategory.name,
        ProductCategory.display_name,
        ProductCategory.type,
        ProductCategory.is_ready,
        ProductCategory.order,
    ]

    column_formatters = {
        ProductCategory.is_ready: lambda m, a: "O" if m.is_ready else "X",
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class ProductHallAdmin(BaseModelViewWithFilters, model=ProductHall):
    name = "웨딩홀"
    name_plural = "웨딩홀 목록"
    icon = "fa-solid fa-building"
    category = "상품 관리"

    column_list = [
        ProductHall.id,
        "product.name",  # 연결된 상품 이름 표시
        ProductHall.address,
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.parking_capacity,
        ProductHall.is_deleted,
    ]

    column_labels = {
        ProductHall.id: "웨딩홀 ID",
        "product.name": "상품명",
        ProductHall.product_id: "상품 ID",
        ProductHall.address: "주소",
        ProductHall.latitude: "위도",
        ProductHall.longitude: "경도",
        ProductHall.min_capacity: "최소 수용 인원",
        ProductHall.max_capacity: "최대 수용 인원",
        ProductHall.parking_capacity: "주차 수용 대수",
        ProductHall.is_deleted: "삭제 여부",
        ProductHall.created_datetime: "생성일시",
        ProductHall.updated_datetime: "수정일시",
        ProductHall.deleted_datetime: "삭제일시",
    }

    column_details_list = [
        ProductHall.id,
        ProductHall.product_id,
        "product.name",
        "product.description",
        "product.available",
        ProductHall.address,
        ProductHall.latitude,
        ProductHall.longitude,
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.parking_capacity,
        ProductHall.is_deleted,
        ProductHall.created_datetime,
        ProductHall.updated_datetime,
        ProductHall.deleted_datetime,
    ]

    column_searchable_list = [
        "product.name",
        ProductHall.address,
    ]

    column_sortable_list = [
        ProductHall.id,
        # "product.name" 정렬은 별도 구현 필요
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.parking_capacity,
        ProductHall.created_datetime,
        ProductHall.updated_datetime,
    ]

    column_formatters = {
        ProductHall.created_datetime: lambda m, a: m.created_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.created_datetime
        else "",
        ProductHall.updated_datetime: lambda m, a: m.updated_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.updated_datetime
        else "",
        ProductHall.deleted_datetime: lambda m, a: m.deleted_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if m.deleted_datetime
        else "",
    }

    # form_excluded_columns = [
    #     ProductHall.created_datetime,
    #     ProductHall.updated_datetime,
    #     ProductHall.deleted_datetime,
    # ]

    # 연결된 Product 모델의 정보를 함께 편집할 수 있도록 설정
    form_columns = [
        "product.name",
        "product.description",
        "product.available",
        "product.product_category_id",
        ProductHall.address,
        ProductHall.latitude,
        ProductHall.longitude,
        ProductHall.min_capacity,
        ProductHall.max_capacity,
        ProductHall.parking_capacity,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # ProductHall이 생성/수정될 때 연결된 Product도 함께 처리
    async def insert_model(self, request: Request, data: dict) -> Any:
        # Product 정보 분리
        product_data = {}
        if "product" in data:
            product_data = data.pop("product")

        # 먼저 Product 생성
        from models import Product

        product = Product(**product_data)
        # 여기서 product를 DB에 추가하는 로직 구현

        # ProductHall에 product_id 설정
        data["product_id"] = product.id

        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk: str, data: dict) -> Any:
        # Product 정보 분리해서 업데이트
        product_data = {}
        if "product" in data:
            product_data = data.pop("product")

        # 기존 ProductHall 객체 가져오기
        obj = await self.get_object_for_details(pk)

        # Product 업데이트 로직 구현
        # ...

        return await super().update_model(request, pk, data)

    async def delete_model(self, request: Request, pk: Any) -> None:
        obj = await self.get_object_for_details(pk)
        obj.is_deleted = True
        # 연결된 Product도 삭제 처리할지 결정
        # obj.product.is_deleted = True
        await self.update_model(request, pk, obj.dict())
