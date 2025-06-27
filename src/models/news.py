from datetime import datetime

import sqlmodel
from sqlmodel import SQLModel, Field, Relationship

from utils.utils import utc_now


class NewsItem(SQLModel, table=True):
    __tablename__ = "news_items"

    id: int | None = Field(default=None, primary_key=True)
    news_category_id: int | None = Field(
        default=None, nullable=False, foreign_key="news_categories.id"
    )
    title: str
    link_url: str
    post_date: datetime = Field(default=utc_now)

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

    news_category: "NewsCategory" = Relationship(back_populates="news_items")


class NewsCategory(SQLModel, table=True):
    __tablename__ = "news_categories"

    id: int | None = Field(default=None, primary_key=True)
    display_name: str = Field(nullable=False)

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

    news_items: list["NewsItem"] = Relationship(back_populates="news_category")
