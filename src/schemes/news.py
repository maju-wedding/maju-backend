from datetime import datetime

from sqlmodel import SQLModel, Field


class NewsCategoryCreate(SQLModel):
    display_name: str = Field(max_length=100)


class NewsCategoryUpdate(SQLModel):
    display_name: str | None = Field(default=None, max_length=100)


class NewsCategoryRead(SQLModel):
    id: int
    display_name: str
    created_datetime: datetime
    news_items_count: int | None = Field(default=0)


class NewsItemCreate(SQLModel):
    news_category_id: int
    title: str = Field(max_length=200)
    link_url: str = Field(max_length=500)
    post_date: datetime | None = Field(default=None)


class NewsItemUpdate(SQLModel):
    news_category_id: int | None = Field(default=None)
    title: str | None = Field(default=None, max_length=200)
    link_url: str | None = Field(default=None, max_length=500)
    post_date: datetime | None = Field(default=None)


class NewsItemRead(SQLModel):
    id: int
    news_category_id: int
    title: str
    link_url: str
    post_date: datetime
    created_datetime: datetime

    # Relationship
    news_category: NewsCategoryRead | None = None
