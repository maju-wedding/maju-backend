from datetime import datetime

from sqlmodel import SQLModel

from schemes.product_categories import ProductCategoryResponse


class ProductCreate(SQLModel):
    category_id: int
    name: str
    description: str
    hashtag: str | None = None

    direct_link: str
    thumbnail_url: str | None = None
    logo_url: str

    enterprise_name: str
    enterprise_code: str

    tel: str
    fax_tel: str

    sido: str
    gugun: str
    dong: str | None = None
    address: str
    lat: float = 0.0
    lng: float = 0.0

    subway_line: str | None = None
    subway_name: str | None = None
    subway_exit: str | None = None

    park_limit: int | None = 0
    park_free_hours: int | None = 0
    way_text: str | None = None

    holiday: str | None = None
    business_hours: str | None = None
    available: bool = True


class ProductUpdate(SQLModel):
    """제품 업데이트를 위한 스키마"""

    product_category_id: int | None = None
    name: str | None = None
    description: str | None = None
    hashtag: str | None = None

    direct_link: str | None = None
    thumbnail_url: str | None = None
    logo_url: str | None = None

    # enterprise
    enterprise_name: str | None = None
    enterprise_code: str | None = None

    # contact
    tel: str | None = None
    fax_tel: str | None = None

    # location
    sido: str | None = None
    gugun: str | None = None
    dong: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None

    # subway
    subway_line: str | None = None
    subway_name: str | None = None
    subway_exit: str | None = None

    park_limit: int | None = None
    park_free_hours: int | None = None
    way_text: str | None = None

    # business
    holiday: str | None = None
    business_hours: str | None = None
    available: bool | None = None


class ProductResponse(SQLModel):
    id: int
    product_category_id: int
    name: str
    description: str
    hashtag: str
    direct_link: str
    thumbnail_url: str
    logo_url: str
    enterprise_name: str
    enterprise_code: str
    tel: str
    fax_tel: str
    sido: str
    gugun: str
    dong: str | None = None
    address: str
    lat: float
    lng: float
    subway_line: str | None = None
    subway_name: str | None = None
    subway_exit: str | None = None
    park_limit: int | None = None
    park_free_hours: int | None = None
    way_text: str | None = None
    holiday: str | None = None
    business_hours: str | None = None
    available: bool
    created_datetime: datetime
    updated_datetime: datetime
    is_deleted: bool

    # Relationships
    category: ProductCategoryResponse | None = None
