from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.checklist_categories import ChecklistCategory
from models.user_spents import UserSpent
from schemes.user_spents import UserSpentCreate, UserSpentUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDUserSpent(CRUDBase[UserSpent, UserSpentCreate, UserSpentUpdate, int]):
    async def create_spent(
        self, db: AsyncSession, *, user_id: UUID, obj_in: UserSpentCreate
    ) -> UserSpent:
        """지출 내역 생성 - 시스템 카테고리 자동 변환"""
        from crud import checklist_category as crud_category

        spent_data = obj_in.model_dump()
        spent_data["user_id"] = user_id

        # 카테고리 처리 (시스템 카테고리인 경우 사용자 카테고리로 변환)
        category = await crud_category.get(db=db, id=spent_data["category_id"])
        if category and category.is_system_category:
            # 사용자의 카테고리 중 동일한 이름을 가진 카테고리 찾기
            user_categories = await crud_category.get_user_categories(
                db=db, user_id=user_id
            )

            matching_categories = [
                cat
                for cat in user_categories
                if cat.display_name == category.display_name
            ]

            if matching_categories:
                # 이미 존재하는 카테고리 사용
                spent_data["category_id"] = matching_categories[0].id
            else:
                # 새 사용자 카테고리 생성
                new_category = await crud_category.create_user_category(
                    db=db,
                    display_name=category.display_name,
                    user_id=user_id,
                )
                spent_data["category_id"] = new_category.id

        # spent_date가 없으면 현재 시간으로 설정
        if not spent_data.get("spent_date"):
            spent_data["spent_date"] = utc_now()

        spent = UserSpent(**spent_data)

        db.add(spent)
        await db.commit()
        await db.refresh(spent)
        return spent

    async def get_user_spent_with_category(
        self, db: AsyncSession, *, spent_id: int, user_id: UUID
    ) -> UserSpent | None:
        """사용자의 특정 지출 내역을 카테고리 정보와 함께 조회"""
        query = (
            select(UserSpent)
            .options(selectinload(UserSpent.category))
            .where(
                and_(
                    UserSpent.id == spent_id,
                    UserSpent.user_id == user_id,
                    UserSpent.is_deleted == False,
                )
            )
        )

        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        category_id: int = None,
    ) -> Sequence[UserSpent]:
        """사용자별 지출 내역 조회"""
        query = (
            select(UserSpent)
            .options(selectinload(UserSpent.category))
            .where(
                and_(
                    UserSpent.user_id == user_id,
                    UserSpent.is_deleted == False,
                )
            )
        )

        if category_id:
            query = query.where(UserSpent.category_id == category_id)

        query = query.order_by(desc(UserSpent.created_datetime))
        query = query.offset(skip).limit(limit)

        result = await db.stream(query)
        return await result.scalars().all()

    async def get_total_spent_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> int:
        """사용자의 총 지출 금액 조회"""
        query = select(func.sum(UserSpent.amount)).where(
            and_(
                UserSpent.user_id == user_id,
                UserSpent.is_deleted == False,
            )
        )

        result = await db.stream(query)
        total = await result.scalar_one_or_none()
        return total or 0

    async def get_spent_by_category(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> list[dict]:
        """카테고리별 지출 요약 조회"""
        query = (
            select(
                ChecklistCategory,
                func.sum(UserSpent.amount).label("total_spent"),
                func.count(UserSpent.id).label("spent_count"),
            )
            .outerjoin(
                UserSpent,
                and_(
                    UserSpent.category_id == ChecklistCategory.id,
                    UserSpent.user_id == user_id,
                    UserSpent.is_deleted == False,
                ),
            )
            .where(
                and_(
                    ChecklistCategory.is_deleted == False,
                    # 사용자의 카테고리이거나 시스템 카테고리
                    (
                        (ChecklistCategory.user_id == user_id)
                        | (ChecklistCategory.is_system_category == True)
                    ),
                )
            )
            .group_by(ChecklistCategory.id)
            .order_by(desc("total_spent"))
        )

        result = await db.stream(query)
        rows = await result.fetchall()

        return [
            {
                "category": row.ChecklistCategory,
                "total_spent": row.total_spent or 0,
                "spent_count": row.spent_count or 0,
            }
            for row in rows
        ]

    async def update_spent(
        self, db: AsyncSession, *, spent_id: int, user_id: UUID, obj_in: UserSpentUpdate
    ) -> UserSpent | None:
        """지출 내역 수정 - 시스템 카테고리 자동 변환"""
        from crud import checklist_category as crud_category

        spent = await self.get_user_spent_with_category(
            db=db, spent_id=spent_id, user_id=user_id
        )

        if not spent:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)

        # 카테고리 변경 시 시스템 카테고리 처리
        if "category_id" in update_data:
            category = await crud_category.get(db=db, id=update_data["category_id"])
            if category and category.is_system_category:
                # 사용자의 카테고리 중 동일한 이름을 가진 카테고리 찾기
                user_categories = await crud_category.get_user_categories(
                    db=db, user_id=user_id
                )

                matching_categories = [
                    cat
                    for cat in user_categories
                    if cat.display_name == category.display_name
                ]

                if matching_categories:
                    # 이미 존재하는 카테고리 사용
                    update_data["category_id"] = matching_categories[0].id
                else:
                    # 새 사용자 카테고리 생성
                    new_category = await crud_category.create_user_category(
                        db=db,
                        display_name=category.display_name,
                        user_id=user_id,
                    )
                    update_data["category_id"] = new_category.id

        update_data["updated_datetime"] = utc_now()

        for field, value in update_data.items():
            setattr(spent, field, value)

        db.add(spent)
        await db.commit()
        await db.refresh(spent)
        return spent

    async def soft_delete_spent(
        self, db: AsyncSession, *, spent_id: int, user_id: UUID
    ) -> UserSpent | None:
        """지출 내역 소프트 삭제"""
        spent = await self.get_user_spent_with_category(
            db=db, spent_id=spent_id, user_id=user_id
        )

        if not spent:
            return None

        spent.is_deleted = True
        spent.deleted_datetime = utc_now()
        spent.updated_datetime = utc_now()

        db.add(spent)
        await db.commit()
        await db.refresh(spent)
        return spent
