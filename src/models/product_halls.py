from sqlmodel import SQLModel, Field, Relationship

from models.products import Product


class ProductHall(SQLModel, table=True):
    __tablename__ = "product_halls"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)

    address: str
    latitude: float
    longitude: float
    min_capacity: int
    max_capacity: int
    parking_capacity: int

    # Relationship
    product: Product = Relationship(back_populates="wedding_hall_detail")
