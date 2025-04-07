from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel

from schemes.product_categories import ProductCategoryResponse


class ProductCreate(SQLModel):
    category_id: int
    name: str
    description: str


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
    dong: str
    address: str
    lat: float
    lng: float
    subway_line: Optional[str] = None
    subway_name: Optional[str] = None
    subway_exit: Optional[str] = None
    park_limit: Optional[int] = None
    park_free_hours: Optional[int] = None
    way_text: Optional[str] = None
    holiday: Optional[str] = None
    business_hours: Optional[str] = None
    available: bool
    created_datetime: datetime
    updated_datetime: datetime
    is_deleted: bool

    # Relationships
    category: Optional[ProductCategoryResponse] = None
