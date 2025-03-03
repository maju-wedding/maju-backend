from schemes.products import ProductCreate


class ProductHallCreate(ProductCreate):
    address: str
    latitude: float
    longitude: float
    min_capacity: int
    max_capacity: int
    parking_capacity: int


class ProductHallCreateInternal(ProductHallCreate):
    product_id: int
