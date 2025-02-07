from sqlmodel import Field, SQLModel


class CategoryBase(SQLModel):
    name: str
    display_name: str


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class CategoryCreate(SQLModel):
    name: str
    display_name: str


class CategoryUpdate(SQLModel):
    name: str | None
    display_name: str | None


class CategoryPublic(CategoryBase):
    id: int
