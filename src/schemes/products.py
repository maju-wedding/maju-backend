from sqlmodel import SQLModel


class ProductCreate(SQLModel):
    category_id: int
    name: str
    description: str
