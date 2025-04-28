from typing import Literal, Any

from sqlmodel import SQLModel


class ResponseWithStatusMessage(SQLModel):
    status: Literal["success", "fail"] = "success"
    message: str | None = None
    data: Any | None = None
