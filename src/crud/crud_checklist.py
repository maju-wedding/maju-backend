from typing import Literal, Any, Sequence
from uuid import UUID

from sqlalchemy import and_, select, func, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from models.checklists import Checklist
from schemes.checklists import ChecklistCreate, ChecklistUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDChecklist(CRUDBase[Checklist, ChecklistCreate, ChecklistUpdate, int]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Checklist]:
        """Get checklists by user ID"""
        query = (
            select(Checklist)
            .where(
                and_(
                    Checklist.user_id == user_id,
                    Checklist.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Checklist.global_display_order)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_category(
        self,
        db: AsyncSession,
        *,
        category_id: int,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
        system_only: bool = False,
        display_order: Literal["global", "category"] = "category",
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """Get checklists by category ID with optional user filter"""
        query = select(Checklist).where(
            and_(
                Checklist.checklist_category_id == category_id,
                Checklist.is_deleted == False,
            )
        )

        if system_only:
            query = query.where(Checklist.is_system_checklist == True)

        if user_id:
            query = query.where(Checklist.user_id == user_id)

        query = (
            query.offset(skip)
            .limit(limit)
            .order_by(
                Checklist.category_display_order
                if display_order == "category"
                else Checklist.global_display_order
            )
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_system_checklists(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Checklist]:
        """Get system checklists (templates)"""
        query = (
            select(Checklist)
            .where(
                and_(
                    Checklist.is_system_checklist == True,
                    Checklist.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_last_global_order(self, db: AsyncSession, *, user_id: UUID) -> int:
        """Get the last global display order for a user"""
        query = select(func.max(Checklist.global_display_order)).where(
            and_(
                Checklist.user_id == user_id,
                Checklist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none() or 0

    async def get_last_category_order(
        self, db: AsyncSession, *, user_id: UUID, category_id: int
    ) -> int:
        """Get the last category display order for a user and category"""
        query = select(func.max(Checklist.category_display_order)).where(
            and_(
                Checklist.user_id == user_id,
                Checklist.checklist_category_id == category_id,
                Checklist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none() or 0

    async def create_from_system_checklist(
        self, db: AsyncSession, *, system_checklist_ids: list[int], user_id: UUID
    ) -> list[Checklist] | None:
        """Create a user checklist from a system checklist template"""
        # Query all system checklists at once
        query = select(Checklist).where(
            and_(
                Checklist.id.in_(system_checklist_ids),
                Checklist.is_system_checklist == True,
                Checklist.is_deleted == False,
            )
        )
        result = await db.execute(query)
        system_checklists = result.scalars().all()

        # Return None if any system checklist is missing
        if len(system_checklists) != len(system_checklist_ids):
            return None

        # Get initial order values
        global_order_base = await self.get_last_global_order(db=db, user_id=user_id)

        # Create mapping of category_id to order for efficiency
        category_orders = {}
        user_checklists = []

        # Create all user checklists
        for index, system_checklist in enumerate(system_checklists):
            category_id = system_checklist.checklist_category_id

            # Only query category order once per category
            if category_id not in category_orders:
                category_orders[category_id] = await self.get_last_category_order(
                    db=db,
                    user_id=user_id,
                    category_id=category_id,
                )

            # Create user checklist
            user_checklist = Checklist(
                title=system_checklist.title,
                description=system_checklist.description,
                checklist_category_id=category_id,
                is_system_checklist=False,
                user_id=user_id,
                global_display_order=global_order_base + index + 1,
                category_display_order=category_orders[category_id] + index + 1,
                created_datetime=utc_now(),
                updated_datetime=utc_now(),
            )

            user_checklists.append(user_checklist)
            db.add(user_checklist)

        # Bulk commit all changes
        await db.commit()

        # Refresh all newly created objects
        for checklist in user_checklists:
            await db.refresh(checklist)

        return user_checklists

    async def update_completion_status(
        self, db: AsyncSession, *, checklist_id: int, is_completed: bool
    ) -> Checklist | None:
        """Update the completion status of a checklist"""
        checklist = await self.get(db, id=checklist_id)
        if not checklist:
            return None

        checklist.is_completed = is_completed
        if is_completed:
            checklist.completed_datetime = utc_now()
        else:
            checklist.completed_datetime = None

        checklist.updated_datetime = utc_now()

        db.add(checklist)
        await db.commit()
        await db.refresh(checklist)
        return checklist

    async def update_display_order(
        self,
        db: AsyncSession,
        *,
        checklist_id: int,
        global_order: int | None = None,
        category_order: int | None = None,
    ) -> Checklist | None:
        """Update display order of a checklist"""
        checklist = await self.get(db, id=checklist_id)
        if not checklist:
            return None

        if global_order is not None:
            checklist.global_display_order = global_order

        if category_order is not None:
            checklist.category_display_order = category_order

        checklist.updated_datetime = utc_now()

        db.add(checklist)
        await db.commit()
        await db.refresh(checklist)
        return checklist

    async def get_system_checklists_by_ids(
        self, db: AsyncSession, *, ids: list[int]
    ) -> Sequence[Checklist]:
        """Get system checklists by IDs"""
        query = select(Checklist).where(
            and_(
                Checklist.id.in_(ids),
                Checklist.is_system_checklist == True,
                Checklist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def create_from_system_checklist_with_category_mapping(
        self,
        db: AsyncSession,
        *,
        system_checklist_ids: list[int],
        user_id: UUID,
        category_mapping: dict[int, int],
    ) -> list[Checklist] | None:
        """Create user checklists from system checklists with category mapping"""
        # Query all system checklists at once
        query = select(Checklist).where(
            and_(
                Checklist.id.in_(system_checklist_ids),
                Checklist.is_system_checklist == True,
                Checklist.is_deleted == False,
            )
        )
        result = await db.execute(query)
        system_checklists = result.scalars().all()

        # Return None if any system checklist is missing
        if len(system_checklists) != len(system_checklist_ids):
            return None

        # Get initial order values
        global_order_base = await self.get_last_global_order(db=db, user_id=user_id)

        # Create mapping of category_id to order for efficiency
        category_orders = {}
        user_checklists = []

        # Create all user checklists
        for index, system_checklist in enumerate(system_checklists):
            system_category_id = system_checklist.checklist_category_id

            # Map system category to user category
            user_category_id = category_mapping.get(system_category_id)
            if not user_category_id:
                continue  # Skip if no mapping found

            # Only query category order once per category
            if user_category_id not in category_orders:
                category_orders[user_category_id] = await self.get_last_category_order(
                    db=db,
                    user_id=user_id,
                    category_id=user_category_id,
                )

            # Create user checklist
            user_checklist = Checklist(
                title=system_checklist.title,
                description=system_checklist.description,
                checklist_category_id=user_category_id,  # Use the mapped category ID
                is_system_checklist=False,
                user_id=user_id,
                global_display_order=global_order_base + index + 1,
                category_display_order=category_orders[user_category_id] + index + 1,
                created_datetime=utc_now(),
                updated_datetime=utc_now(),
            )

            user_checklists.append(user_checklist)
            db.add(user_checklist)

        # Bulk commit all changes
        await db.commit()

        # Refresh all newly created objects
        for checklist in user_checklists:
            await db.refresh(checklist)

        return user_checklists

    async def soft_delete_all_by_user(self, db: AsyncSession, *, user_id: UUID) -> int:
        """Soft delete all checklists for a user

        Returns:
            int: Number of checklists marked as deleted
        """
        # Update all non-deleted checklists for the user
        query = select(Checklist).where(
            and_(
                Checklist.user_id == user_id,
                Checklist.is_deleted == False,
            )
        )
        result = await db.execute(query)
        checklists = result.scalars().all()

        count = 0
        for checklist in checklists:
            checklist.is_deleted = True
            checklist.deleted_datetime = utc_now()
            checklist.updated_datetime = utc_now()
            db.add(checklist)
            count += 1

        # Commit all changes at once
        if count > 0:
            await db.commit()

        return count
