from sqlmodel import SQLModel

from core.enums import CategoryTypeEnum


class ProductCategoryCreate(SQLModel):
    name: str
    display_name: str
    order: int


class ProductCategoryUpdate(SQLModel):
    name: str | None = None
    display_name: str | None = None
    order: int | None = None


class ProductCategoryRead(SQLModel):
    id: int
    name: str
    display_name: str
    type: CategoryTypeEnum
    is_ready: bool
    order: int


class ProductCategoryResponse(ProductCategoryRead):
    pass
