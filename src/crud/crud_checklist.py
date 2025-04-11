from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.checklists import Checklist
from schemes.checklists import ChecklistCreate, ChecklistUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDChecklist(CRUDBase[Checklist, ChecklistCreate, ChecklistUpdate, int]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Checklist]:
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
        limit: int = 100
    ) -> list[Checklist]:
        """Get checklists by category ID with optional user filter"""
        query = select(Checklist).where(
            and_(
                Checklist.checklist_category_id == category_id,
                Checklist.is_deleted == False,
            )
        )

        if user_id:
            query = query.where(Checklist.user_id == user_id)

        query = query.offset(skip).limit(limit)
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_system_checklists(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[Checklist]:
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
        self, db: AsyncSession, *, system_checklist_id: int, user_id: UUID
    ) -> Checklist:
        """Create a user checklist from a system checklist template"""
        # Get system checklist
        query = select(Checklist).where(
            and_(
                Checklist.id == system_checklist_id,
                Checklist.is_system_checklist == True,
                Checklist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        system_checklist = await result.scalar_one_or_none()

        if not system_checklist:
            return None

        # Get orders for new checklist
        global_order = await self.get_last_global_order(db=db, user_id=user_id)

        category_order = await self.get_last_category_order(
            db=db, user_id=user_id, category_id=system_checklist.checklist_category_id
        )

        # Create user checklist
        user_checklist = Checklist(
            title=system_checklist.title,
            description=system_checklist.description,
            checklist_category_id=system_checklist.checklist_category_id,
            is_system_checklist=False,
            user_id=user_id,
            global_display_order=global_order + 1,
            category_display_order=category_order + 1,
            created_datetime=utc_now(),
            updated_datetime=utc_now(),
        )

        db.add(user_checklist)
        await db.commit()
        await db.refresh(user_checklist)
        return user_checklist

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
        category_order: int | None = None
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
