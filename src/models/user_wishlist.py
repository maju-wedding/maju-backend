from datetime import datetime
from uuid import UUID

import sqlmodel
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from models.products import Product
from utils.utils import utc_now


class UserWishlist(SQLModel, table=True):
    __tablename__ = "user_wishlists"

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    product_id: int = Field(foreign_key="products.id")
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    memo: str | None = None
    is_deleted: bool = Field(default=False)

    # Relationship
    product: Product = Relationship(back_populates="wishlists")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="unique_user_product"),
    )


class WishlistCreate(SQLModel):
    product_id: int


class WishlistCreateInternal(SQLModel):
    user_id: UUID
    product_id: int
