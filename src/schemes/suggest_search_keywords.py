from sqlmodel import SQLModel


class SuggestSearchKeywordRead(SQLModel):
    id: int
    keyword: str
