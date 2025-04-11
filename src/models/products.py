from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlmodel
from sqlalchemy import Text
from sqlmodel import Field, Relationship, SQLModel

from utils.utils import utc_now

if TYPE_CHECKING:
    from models.product_images import ProductImage
    from models.product_ai_review import ProductAIReview
    from models.product_categories import ProductCategory
    from models.product_halls import ProductHall
    from models.product_scores import ProductScore
    from models.user_wishlist import UserWishlist


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    product_category_id: int = Field(foreign_key="product_categories.id")
    name: str = Field(max_length=100)
    description: str = Field(Text)
    hashtag: str | None = Field(max_length=100, default=None)

    direct_link: str = Field(max_length=500)
    # images
    thumbnail_url: str | None = Field(max_length=500, default=None)
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
    dong: str | None = Field(max_length=30, default=None)
    address: str = Field(max_length=100)
    lat: float = Field(default=0.0)
    lng: float = Field(default=0.0)

    # subway
    subway_line: str | None = Field(max_length=30, default=None)
    subway_name: str | None = Field(max_length=30, default=None)
    subway_exit: str | None = Field(max_length=30, default=None)

    park_limit: int | None = Field(default=0)
    park_free_hours: int | None = Field(default=0)
    way_text: str | None = Field(max_length=100, default=None)

    # business
    holiday: str | None = Field(max_length=100, default=None)
    business_hours: str | None = Field(max_length=100, default=None)
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
    ai_reviews: list["ProductAIReview"] = Relationship(back_populates="product")
    scores: list["ProductScore"] = Relationship(back_populates="product")
    images: list["ProductImage"] = Relationship(back_populates="product")

    product_hall: Optional["ProductHall"] = Relationship(back_populates="product")
    # studio_detail: Optional["StudioDetail"] = Relationship(back_populates="product")
    # dress_detail: Optional["DressDetail"] = Relationship(back_populates="product")
    # makeup_detail: Optional["MakeupDetail"] = Relationship(back_populates="product")
