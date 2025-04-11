
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_categories import ProductCategory
from models.products import Product
from schemes.product_categories import ProductCategoryCreate, ProductCategoryUpdate
from utils.utils import utc_now
from .base import CRUDBase


class CRUDProductCategory(
    CRUDBase[ProductCategory, ProductCategoryCreate, ProductCategoryUpdate, int]
):
    async def get_all_active(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ProductCategory]:
        """Get all active product categories"""
        query = (
            select(ProductCategory)
            .where(ProductCategory.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_name(
        self, db: AsyncSession, *, name: str
    ) -> ProductCategory | None:
        """Get category by name"""
        query = select(ProductCategory).where(
            and_(
                ProductCategory.name == name,
                ProductCategory.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_last_order(self, db: AsyncSession) -> int:
        """Get the highest order value among categories"""
        query = select(func.max(ProductCategory.order)).where(
            ProductCategory.is_deleted == False
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none() or 0

    async def create_with_order(
        self, db: AsyncSession, *, obj_in: ProductCategoryCreate
    ) -> ProductCategory:
        """Create a category with automatic order increment"""
        # Get last order
        last_order = await self.get_last_order(db)

        # Create category with incremented order
        category_data = obj_in.model_dump()
        category_data["order"] = last_order + 1

        category = ProductCategory(**category_data)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    async def soft_delete_with_products(
        self, db: AsyncSession, *, category_id: int
    ) -> None:
        """Soft delete a category and its related products"""
        # Get category
        category = await self.get(db, id=category_id)
        if not category:
            return None

        # Get related products
        query = select(Product).where(
            and_(
                Product.product_category_id == category_id,
                Product.is_deleted == False,
            )
        )
        result = await db.stream(query)
        products = await result.scalars().all()

        # Soft delete category and products
        current_time = utc_now()

        category.is_deleted = True
        category.deleted_datetime = current_time
        category.updated_datetime = current_time

        for product in products:
            product.is_deleted = True
            product.deleted_datetime = current_time
            product.updated_datetime = current_time

        await db.commit()
        return category
