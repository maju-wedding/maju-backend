from datetime import datetime

import sqlmodel
from sqlmodel import SQLModel, Field


class DateTimeMixin(SQLModel):
    created_datetime: datetime = Field(
        default=datetime.now(),
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    updated_datetime: datetime = Field(
        default=datetime.now(),
        sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True)),
    )
    deleted_datetime: datetime | None = Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
