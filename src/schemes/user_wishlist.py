from uuid import UUID
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlmodel import SQLModel

from schemes.products import ProductResponse


class WishlistCreate(SQLModel):
    product_id: int
    memo: Optional[str] = None


class WishlistCreateInternal(SQLModel):
    user_id: UUID
    product_id: int
    memo: Optional[str] = None


class WishlistUpdate(SQLModel):
    memo: Optional[str] = None


class WishlistResponse(SQLModel):
    id: int
    user_id: UUID
    product_id: int
    memo: Optional[str] = None
    created_datetime: datetime
    is_deleted: bool


class WishlistDetailResponse(WishlistResponse):
    product: ProductResponse


class WishlistListResponse(BaseModel):
    total: int
    items: List[WishlistDetailResponse]
