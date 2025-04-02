from datetime import datetime

import sqlmodel
from sqlmodel import SQLModel, Field

from utils.utils import utc_now


class SuggestSearchKeyword(SQLModel, table=True):
    __tablename__ = "suggest_search_keywords"

    id: int | None = Field(default=None, primary_key=True)
    keyword: str = Field(...)

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
