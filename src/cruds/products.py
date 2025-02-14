from fastcrud import FastCRUD

from models import Product


class ProductCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


products_crud = ProductCRUD(Product)
