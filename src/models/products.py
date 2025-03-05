from datetime import datetime
from typing import Optional, TYPE_CHECKING

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now

if TYPE_CHECKING:
    from models import ProductCategory
    from models.product_halls import ProductHall
    from models.user_wishlist import UserWishlist


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    product_category_id: int = Field(foreign_key="product_categories.id")
    name: str = Field(max_length=100)
    description: str
    hashtag: str = Field(max_length=100)

    direct_link: str = Field(max_length=500)
    # images
    thumbnail: str = Field(max_length=500)
    logo_url: str = Field(max_length=500)

    # enterprise
    enterprise_name: str = Field(max_length=100)
    enterprise_code: str = Field(max_length=100)

    # contact
    tel: str = Field(max_length=20)
    fax_tel: str = Field(max_length=20)

    # location
    sido: str = Field(max_length=20)
    gugun: str = Field(max_length=20)
    dong: str = Field(max_length=20)
    address: str = Field(max_length=100)
    lat: float = Field(default=0.0)
    lng: float = Field(default=0.0)

    # subway
    subway_line: str = Field(max_length=20)
    subway_name: str = Field(max_length=20)
    subway_exit: str = Field(max_length=20)

    park_limit: int = Field(default=0)
    park_free_hours: int = Field(default=0)
    way_text: str = Field(max_length=100)

    # business
    holiday: str = Field(max_length=100)
    business_hours: str = Field(max_length=100)
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

    # studio_detail: Optional["StudioDetail"] = Relationship(back_populates="product")
    # dress_detail: Optional["DressDetail"] = Relationship(back_populates="product")
    # makeup_detail: Optional["MakeupDetail"] = Relationship(back_populates="product")
