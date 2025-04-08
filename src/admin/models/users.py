from typing import Any

from starlette.requests import Request

from admin.models.base import BaseModelViewWithFilters
from core.security import get_password_hash
from models import User
from utils.utils import utc_now


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
        User.wedding_datetime,
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
        User.wedding_datetime: "예식일",
        User.is_active: "활성 여부",
        User.is_superuser: "관리자 여부",
        User.social_provider: "소셜 제공자",
        User.is_deleted: "삭제 여부",
        User.joined_datetime: "가입일시",
        User.updated_datetime: "수정일시",
        User.deleted_datetime: "삭제일시",
        User.service_policy_agreement: "서비스 정책 동의",
        User.privacy_policy_agreement: "개인정보 정책 동의",
        User.advertising_agreement: "광고 마케팅 수신 동의",
    }

    column_details_list = [
        User.id,
        User.email,
        User.nickname,
        User.phone_number,
        User.user_type,
        User.wedding_datetime,
        User.social_provider,
        User.is_active,
        User.is_superuser,
        User.is_deleted,
        User.joined_datetime,
        User.updated_datetime,
        User.deleted_datetime,
        User.service_policy_agreement,
        User.privacy_policy_agreement,
        User.advertising_agreement,
    ]

    column_searchable_list = [
        User.email,
        User.nickname,
    ]

    column_sortable_list = [
        User.id,
        User.joined_datetime,
    ]

    column_formatters = {
        User.wedding_datetime: lambda m, a: (
            m.joined_datetime.strftime("%Y-%m-%d %H:%M:%S") if m.joined_datetime else ""
        ),
    }

    column_formatters_detail = {
        User.wedding_datetime: lambda m, a: (
            m.joined_datetime.strftime("%Y-%m-%d %H:%M:%S") if m.joined_datetime else ""
        ),
        User.joined_datetime: lambda m, a: (
            m.joined_datetime.strftime("%Y-%m-%d %H:%M:%S") if m.joined_datetime else ""
        ),
        User.updated_datetime: lambda m, a: (
            m.updated_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.updated_datetime
            else ""
        ),
        User.deleted_datetime: lambda m, a: (
            m.deleted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.deleted_datetime
            else ""
        ),
    }

    form_excluded_columns = [
        User.is_deleted,
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
        "advertising_agreement",
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
        obj.is_active = False
        obj.deleted_datetime = utc_now()
        await self.update_model(request, pk, obj.dict())
