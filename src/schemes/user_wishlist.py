from uuid import UUID

from sqlmodel import SQLModel


class WishlistCreate(SQLModel):
    product_id: int


class WishlistCreateInternal(SQLModel):
    user_id: UUID
    product_id: int
