from fastcrud import FastCRUD

from models import Product, ProductHall


class ProductCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


products_crud = ProductCRUD(Product)
products_halls_crud = ProductCRUD(ProductHall)
