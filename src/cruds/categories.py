from fastcrud import FastCRUD

from models import Category


class CategoryCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


categories_crud = CategoryCRUD(Category)
