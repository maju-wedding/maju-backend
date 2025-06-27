from datetime import datetime

from sqlmodel import SQLModel, Field


class MagazineCreate(SQLModel):
    title: str = Field(max_length=200)
    thumbnail_url: str = Field(max_length=500)
    content_image_urls: list[str] = Field(default_factory=list)


class MagazineUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=200)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    content_image_urls: list[str] | None = Field(default=None)


class MagazineRead(SQLModel):
    id: int
    title: str
    thumbnail_url: str
    content_image_urls: list[str]
    created_datetime: datetime
    updated_datetime: datetime
