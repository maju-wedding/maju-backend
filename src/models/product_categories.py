from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel, Relationship

from core.enums import CategoryTypeEnum

if TYPE_CHECKING:
    from models import Product


class ProductCategory(SQLModel, table=True):
    __tablename__ = "product_categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=20)
    display_name: str = Field(max_length=10)
    type: CategoryTypeEnum = Field(sa_column=Column(String))
    is_ready: bool = Field(default=False)
    order: int = Field(default=0, ge=0)

    products: list["Product"] = Relationship(back_populates="category")
