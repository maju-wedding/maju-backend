from sqladmin import ModelView
from sqlmodel import select


class BaseModelViewWithFilters(ModelView):
    """필터링 기능이 추가된 기본 ModelView 클래스"""

    page_size = 10
    page_size_options = [10, 20, 50, 100]

    def list_query(self, request):
        query = select(self.model)

        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")

        # 삭제 상태 필터
        is_deleted_param = request.query_params.get("is_deleted")
        if is_deleted_param == "true":
            query = query.where(self.model.is_deleted == True)
        elif is_deleted_param == "false":
            query = query.where(self.model.is_deleted == False)
        elif is_deleted_param is None:
            query = query.where(self.model.is_deleted == False)

        query = query.order_by(self.model.id)

        if page:
            query = query.offset((int(page) - 1) * self.page_size)
        if page_size:
            query = query.limit(int(page_size))

        return query
