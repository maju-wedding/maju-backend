from sqlmodel import Field, SQLModel


class CategoryBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)
    display_name: str = Field(max_length=10)


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class CategoryCreate(SQLModel):
    name: str
    display_name: str


class CategoryUpdate(SQLModel):
    name: str | None = None
    display_name: str | None = None


class CategoryRead(CategoryBase):
    id: int
