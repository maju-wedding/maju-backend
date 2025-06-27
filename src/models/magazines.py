from datetime import datetime

import sqlmodel
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field

from utils.utils import utc_now


class Magazine(SQLModel, table=True):
    __tablename__ = "magazines"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    thumbnail_url: str
    content_image_urls: list[str] = Field(default_factory=list, sa_column=Column(JSON))

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
