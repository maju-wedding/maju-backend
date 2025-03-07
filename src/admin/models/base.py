from sqladmin import ModelView
from sqlalchemy.orm import joinedload
from sqlmodel import select


class BaseModelViewWithFilters(ModelView):
    """필터링 기능이 추가된 기본 ModelView 클래스"""

    page_size = 10
    page_size_options = [10, 20, 50, 100]

    relation_prefixes = {
        "product.": "product",
        "checklist_category.": "checklist_category",
        "enterprise.": "enterprise",
        "user.": "user",
        # 필요한 다른 관계들 추가
    }

    def list_query(self, request):
        query = select(self.model)

        used_relations = set()
        for col in self.column_list:
            if isinstance(col, str):
                for prefix, attr in self.relation_prefixes.items():
                    if col.startswith(prefix):
                        used_relations.add(attr)
                        break

        for relation in used_relations:
            query = query.options(joinedload(getattr(self.model, relation)))

        # Filter
        is_deleted_param = request.query_params.get("is_deleted")
        if is_deleted_param == "true":
            query = query.where(self.model.is_deleted == True)
        elif is_deleted_param == "false":
            query = query.where(self.model.is_deleted == False)
        elif is_deleted_param is None:
            query = query.where(self.model.is_deleted == False)

        # Pagination
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", self.page_size)
        query = query.offset((int(page) - 1) * self.page_size)
        query = query.limit(int(page_size))

        return query
