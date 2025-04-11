from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_wishlist import UserWishlist
from schemes.user_wishlist import WishlistCreate, WishlistUpdate
from .base import CRUDBase


class CRUDUserWishlist(CRUDBase[UserWishlist, WishlistCreate, WishlistUpdate, int]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[UserWishlist]:
        """Get wishlists by user ID"""
        query = (
            select(UserWishlist)
            .where(
                and_(
                    UserWishlist.user_id == user_id,
                    UserWishlist.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_user_and_product(
        self, db: AsyncSession, *, user_id: UUID, product_id: int
    ) -> UserWishlist | None:
        """Get wishlist by user ID and product ID"""
        query = select(UserWishlist).where(
            and_(
                UserWishlist.user_id == user_id,
                UserWishlist.product_id == product_id,
                UserWishlist.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()
