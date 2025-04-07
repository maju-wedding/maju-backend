from fastcrud import FastCRUD
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from models import UserWishlist
from schemes.user_wishlist import WishlistCreateInternal, WishlistUpdate


class UserWishlistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user_wishlists(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ):
        """사용자의 위시리스트를 가져옵니다."""
        query = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_deleted == False,
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def count_user_wishlists(self, db: AsyncSession, user_id: UUID):
        """사용자의 위시리스트 수를 세는 함수입니다."""
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == False,
        )
        result = await db.execute(query)
        return len(result.scalars().all())

    async def get_wishlist_by_user_and_product(
        self, db: AsyncSession, user_id: UUID, product_id: int
    ):
        """사용자의 특정 제품 위시리스트를 가져옵니다."""
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.product_id == product_id,
            self.model.is_deleted == False,
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def create_wishlist(self, db: AsyncSession, obj_in: WishlistCreateInternal):
        """위시리스트를 생성합니다."""
        return await self.create(db=db, obj_in=obj_in)

    async def update_wishlist_memo(
        self, db: AsyncSession, wishlist_id: int, obj_in: WishlistUpdate
    ):
        """위시리스트의 메모를 업데이트합니다."""
        stmt = (
            update(self.model)
            .where(self.model.id == wishlist_id)
            .values(**obj_in.dict(exclude_unset=True))
        )
        await db.execute(stmt)
        await db.commit()
        return await self.get(db=db, id=wishlist_id)

    async def soft_delete(self, db: AsyncSession, wishlist_id: int):
        """위시리스트를 소프트 삭제합니다."""
        stmt = (
            update(self.model)
            .where(self.model.id == wishlist_id)
            .values(is_deleted=True)
        )
        await db.execute(stmt)
        await db.commit()


user_wishlists_crud = UserWishlistCRUD(UserWishlist)
