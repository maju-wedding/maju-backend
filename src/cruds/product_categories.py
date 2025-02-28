from fastcrud import FastCRUD

from models import ProductCategory


class ProductCategoryCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


product_categories_crud = ProductCategoryCRUD(ProductCategory)
