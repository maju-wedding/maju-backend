from datetime import datetime
from typing import Optional, TYPE_CHECKING

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models import Category
    from models.product_halls import ProductHall
    from models.user_wishlist import UserWishlist


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.id")
    name: str
    description: str
    available: bool = True
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    is_deleted: bool = Field(default=False)

    # Relationships
    category: "Category" = Relationship(back_populates="products")
    wishlists: list["UserWishlist"] = Relationship(back_populates="product")
    wedding_hall_detail: Optional["ProductHall"] = Relationship(
        back_populates="product"
    )

    # studio_detail: Optional["StudioDetail"] = Relationship(back_populates="product")
    # dress_detail: Optional["DressDetail"] = Relationship(back_populates="product")
    # makeup_detail: Optional["MakeupDetail"] = Relationship(back_populates="product")


class ProductCreate(SQLModel):
    category_id: int
    name: str
    description: str
