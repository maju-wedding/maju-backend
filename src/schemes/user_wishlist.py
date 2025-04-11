from uuid import UUID
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import SQLModel

from schemes.products import ProductResponse


class WishlistCreate(SQLModel):
    product_id: int
    memo: str | None = None


class WishlistCreateInternal(SQLModel):
    user_id: UUID
    product_id: int
    memo: str | None = None


class WishlistUpdate(SQLModel):
    memo: str | None = None


class WishlistResponse(SQLModel):
    id: int
    user_id: UUID
    product_id: int
    memo: str | None = None
    created_datetime: datetime
    is_deleted: bool


class WishlistDetailResponse(WishlistResponse):
    product: ProductResponse


class WishlistListResponse(BaseModel):
    total: int
    items: list[WishlistDetailResponse]
