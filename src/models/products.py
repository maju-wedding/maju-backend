from datetime import datetime
from typing import Optional, TYPE_CHECKING

import sqlmodel
from sqlalchemy import Text
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_ai_review import ProductAIReview
    from models.product_categories import ProductCategory
    from models.product_halls import ProductHall
    from models.user_wishlist import UserWishlist


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    product_category_id: int = Field(foreign_key="product_categories.id")
    name: str = Field(max_length=100)
    description: str = Field(Text)
    hashtag: str = Field(max_length=100)

    direct_link: str = Field(max_length=500)
    # images
    thumbnail: str = Field(max_length=500)
    logo_url: str = Field(max_length=500)

    # enterprise
    enterprise_name: str = Field(max_length=100)
    enterprise_code: str = Field(max_length=100)

    # contact
    tel: str = Field(max_length=30)
    fax_tel: str = Field(max_length=30)

    # location
    sido: str = Field(max_length=30)
    gugun: str = Field(max_length=30)
    dong: str = Field(max_length=30)
    address: str = Field(max_length=100)
    lat: float = Field(default=0.0)
    lng: float = Field(default=0.0)

    # subway
    subway_line: str | None = Field(max_length=30, nullable=True)
    subway_name: str | None = Field(max_length=30, nullable=True)
    subway_exit: str | None = Field(max_length=30, nullable=True)

    park_limit: int | None = Field(default=0, nullable=True)
    park_free_hours: int | None = Field(default=0, nullable=True)
    way_text: str | None = Field(max_length=100, nullable=True)

    # business
    holiday: str | None = Field(max_length=100, nullable=True)
    business_hours: str | None = Field(max_length=100, nullable=True)
    available: bool = Field(default=True)

    is_deleted: bool = Field(default=False)
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )

    # Relationships
    category: "ProductCategory" = Relationship(back_populates="products")
    wishlists: list["UserWishlist"] = Relationship(back_populates="product")
    wedding_hall_detail: Optional["ProductHall"] = Relationship(
        back_populates="product"
    )
    ai_reviews: list["ProductAIReview"] = Relationship(back_populates="product")

    # studio_detail: Optional["StudioDetail"] = Relationship(back_populates="product")
    # dress_detail: Optional["DressDetail"] = Relationship(back_populates="product")
    # makeup_detail: Optional["MakeupDetail"] = Relationship(back_populates="product")


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    image_url: str = Field(max_length=500)
    order: int = Field(default=0, ge=0)
    is_deleted: bool = Field(default=False)
    created_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default_factory=utc_now,
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
