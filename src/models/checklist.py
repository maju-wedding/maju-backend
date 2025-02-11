from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from models import Category


class DefaultChecklistItem(SQLModel, table=True):
    """기본 제공되는 체크리스트 아이템"""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    recommended_timeline: int | None = Field(
        default=None, description="결혼일 기준 몇일 전까지"
    )

    # Foreign Keys
    category_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    category: Category | None = Relationship(back_populates="default_items")


class UserChecklist(SQLModel, table=True):
    """사용자별 체크리스트"""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    wedding_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    items: list["CustomChecklistItem"] = Relationship(back_populates="checklist")


class CustomChecklistItem(SQLModel, table=True):
    """사용자가 커스터마이징한 체크리스트 아이템"""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    deadline: datetime | None = None
    is_completed: bool = Field(default=False)
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 기본 체크리스트 아이템에서 복사된 경우
    default_item_id: int | None = Field(
        default=None, foreign_key="defaultchecklistitem.id"
    )

    # Foreign Keys
    checklist_id: int = Field(foreign_key="userchecklist.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    checklist: UserChecklist = Relationship(back_populates="items")
    category: Category | None = Relationship(back_populates="custom_items")
