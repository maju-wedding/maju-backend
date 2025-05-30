from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import and_, select, func, Row
from sqlalchemy.ext.asyncio import AsyncSession

from models.categories import Category
from models.checklists import Checklist
from schemes.checklists import CategoryCreate, CategoryUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate, int]):
    async def get_system_categories(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Category]:
        """Get system-provided checklist categories"""
        query = (
            select(Category)
            .where(
                and_(
                    Category.is_system_category == True,
                    Category.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_user_categories(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Category]:
        """Get user-created checklist categories"""
        query = (
            select(Category)
            .where(
                and_(
                    Category.user_id == user_id,
                    Category.is_deleted == False,
                ),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_user_categories_with_checklist_count(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ):
        """Get categories with count of checklists in each"""
        query = (
            select(Category, func.count(Checklist.id).label("checklist_count"))
            .outerjoin(
                Checklist,
                and_(
                    Checklist.category_id == Category.id,
                    Checklist.user_id == user_id,
                    Checklist.is_deleted == False,
                ),
            )
            .where(
                and_(
                    Category.is_deleted == False,
                    Category.user_id == user_id,
                )
            )
            .group_by(Category.id)
        )

        query = query.offset(skip).limit(limit).order_by(Category.id)
        result = await db.stream(query)
        return await result.fetchall()

    async def get_user_category(
        self, db: AsyncSession, *, category_id: int, user_id: UUID
    ) -> Category | None:
        """Get a user's category by ID"""
        query = select(Category).where(
            and_(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_categories_with_checklist_count(
        self,
        db: AsyncSession,
        *,
        user_id: UUID | None = None,
        system_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Row[tuple[Any, ...] | Any]]:
        """Get categories with count of checklists in each"""
        query = (
            select(Category, func.count(Checklist.id).label("checklist_count"))
            .outerjoin(
                Checklist,
                and_(
                    Checklist.category_id == Category.id,
                    Checklist.is_deleted == False,
                ),
            )
            .where(Category.is_deleted == False)
            .group_by(Category.id)
        )

        if system_only:
            query = query.where(Category.is_system_category == True)
        elif user_id:
            query = query.where(
                and_(
                    Category.is_system_category == True,
                    Category.user_id == user_id,
                )
            )

        query = query.offset(skip).limit(limit).order_by(Category.id)
        result = await db.stream(query)
        return await result.fetchall()

    async def get_category_with_checklist_count(
        self, db: AsyncSession, *, category_id: int
    ) -> tuple[Category | None, int]:
        """Get a category with its checklist count"""
        query = (
            select(Category, func.count(Checklist.id).label("checklist_count"))
            .outerjoin(
                Checklist,
                and_(
                    Checklist.category_id == Category.id,
                    Checklist.is_deleted == False,
                ),
            )
            .where(
                and_(
                    Category.id == category_id,
                    Category.is_deleted == False,
                )
            )
            .group_by(Category.id)
        )

        result = await db.stream(query)
        row = await result.first()

        if not row:
            return None, 0

        return row.Category, row.checklist_count

    async def get_user_category_with_checklist_count(
        self, db: AsyncSession, *, category_id: int, user_id: UUID
    ) -> tuple[Category | None, int]:
        """Get a user's category with its checklist count"""
        query = (
            select(Category, func.count(Checklist.id).label("checklist_count"))
            .outerjoin(
                Checklist,
                and_(
                    Checklist.category_id == Category.id,
                    Checklist.is_deleted == False,
                    Checklist.user_id == user_id,
                ),
            )
            .where(
                and_(
                    Category.id == category_id,
                    Category.user_id == user_id,
                    Category.is_deleted == False,
                )
            )
            .group_by(Category.id)
        )

        result = await db.stream(query)
        row = await result.first()

        if not row:
            return None, 0

        return row.Category, row.checklist_count

    async def get_system_categories_with_checklists(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get system categories with their checklists"""
        from crud import checklist as crud_checklist

        # 1. Get system categories
        categories = await self.get_system_categories(db=db, skip=skip, limit=limit)

        # 2. For each category, get checklists
        result = []
        for category in categories:
            # Get checklists for this category
            checklists = await crud_checklist.get_by_category(
                db=db, category_id=category.id, system_only=True, display_order="global"
            )

            # Format category with checklists
            category_data = {
                "id": category.id,
                "display_name": category.display_name,
                "user_id": category.user_id,
                "is_system_category": category.is_system_category,
                "checklists": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "description": c.description,
                        "global_display_order": c.global_display_order,
                    }
                    for c in checklists
                ],
            }

            result.append(category_data)

        return result

    async def create_system_category(
        self, db: AsyncSession, *, display_name: str
    ) -> Category:
        """Create a system checklist category"""
        category = Category(
            display_name=display_name,
            is_system_category=True,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    async def create_user_category(
        self,
        db: AsyncSession,
        *,
        display_name: str,
        user_id: UUID,
        icon_url: str | None = None,
    ) -> Category:
        """Create a user checklist category"""
        category = Category(
            display_name=display_name,
            icon_url=icon_url,
            is_system_category=False,
            user_id=user_id,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    async def soft_delete_with_checklists(
        self, db: AsyncSession, *, category_id: int
    ) -> Category | None:
        """Soft delete a category and all its checklists"""
        # Get the category
        category = await self.get(db, id=category_id)
        if not category:
            return None

        # Get all checklists in this category
        query = select(Checklist).where(
            and_(
                Checklist.category_id == category_id,
                Checklist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        checklists = await result.scalars().all()

        # Soft delete all checklists
        current_time = utc_now()
        for checklist in checklists:
            checklist.is_deleted = True
            checklist.deleted_datetime = current_time
            checklist.updated_datetime = current_time

        # Soft delete the category
        category.is_deleted = True
        category.deleted_datetime = current_time
        category.updated_datetime = current_time

        await db.commit()
        return category

    async def soft_delete_all_by_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> tuple[int, int]:
        """Soft delete all checklist categories for a user and their checklists

        Returns:
            tuple[int, int]: Tuple of (number of categories deleted, number of checklists deleted)
        """
        # 1. Get all categories for the user that are not deleted
        query = select(Category).where(
            and_(
                Category.user_id == user_id,
                Category.is_deleted == False,
            )
        )
        result = await db.execute(query)
        categories = result.scalars().all()

        # If no categories, return early
        if not categories:
            return 0, 0

        # 2. Get category IDs
        category_ids = [category.id for category in categories]

        # 3. Find all checklists in these categories
        checklist_query = select(Checklist).where(
            and_(
                Checklist.category_id.in_(category_ids),
                Checklist.user_id == user_id,
                Checklist.is_deleted == False,
            )
        )
        checklist_result = await db.execute(checklist_query)
        checklists = checklist_result.scalars().all()

        # 4. Mark checklists as deleted
        checklist_count = 0
        current_time = utc_now()
        for checklist in checklists:
            checklist.is_deleted = True
            checklist.deleted_datetime = current_time
            checklist.updated_datetime = current_time
            db.add(checklist)
            checklist_count += 1

        # 5. Mark categories as deleted
        category_count = 0
        for category in categories:
            category.is_deleted = True
            category.deleted_datetime = current_time
            category.updated_datetime = current_time
            db.add(category)
            category_count += 1

        # 6. Commit all changes at once
        await db.commit()

        return category_count, checklist_count
