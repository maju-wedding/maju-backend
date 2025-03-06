from sqladmin import ModelView
from sqlmodel import select


class BaseModelViewWithFilters(ModelView):
    """필터링 기능이 추가된 기본 ModelView 클래스"""

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
