from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel, Relationship

from core.enums import CategoryTypeEnum

if TYPE_CHECKING:
    from models import Product


class CategoryBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)
    display_name: str = Field(max_length=10)
    type: CategoryTypeEnum = Field(sa_column=Column(String))
    is_ready: bool = Field(default=False)
    order: int = Field(default=0, ge=0)


class Category(CategoryBase, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)

    products: list["Product"] = Relationship(back_populates="category")


class CategoryCreate(SQLModel):
    name: str
    display_name: str
    order: int


class CategoryUpdate(SQLModel):
    name: str | None = None
    display_name: str | None = None
    order: int | None = None


class CategoryRead(CategoryBase):
    id: int
