from fastcrud import FastCRUD

from models import SuggestSearchKeyword


class SuggestSearchKeywordCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


suggest_search_keywords_crud = SuggestSearchKeywordCRUD(SuggestSearchKeyword)
