from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from models import ProductCategory, Product
from schemes.product_categories import ProductCategoryCreate, ProductCategoryUpdate
from utils.utils import utc_now

router = APIRouter()


@router.get("")
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 목록 조회"""
    query = (
        select(ProductCategory)
        .where(ProductCategory.is_deleted == False)
        .offset(skip)
        .limit(limit)
    )
    result = await session.stream(query)
    categories = await result.scalars().all()
    return categories


@router.get("/{category_id}")
async def get_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 상세 조회"""
    query = select(ProductCategory).where(
        and_(
            ProductCategory.id == category_id,
            ProductCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("")
async def create_category(
    category_create: ProductCategoryCreate,
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 생성"""
    # Get last order
    query = select(func.max(ProductCategory.order)).where(
        ProductCategory.is_deleted == False,
    )
    result = await session.stream(query)
    last_order = await result.scalar_one_or_none() or 0

    # Create category
    category = ProductCategory(
        name=category_create.name,
        display_name=category_create.display_name,
        type=category_create.type,
        order=last_order + 1,
        created_datetime=utc_now(),
        updated_datetime=utc_now(),
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@router.put("/{category_id}")
async def update_category(
    category_id: int = Path(...),
    category_update: ProductCategoryUpdate = None,
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 수정"""
    query = select(ProductCategory).where(
        and_(
            ProductCategory.id == category_id,
            ProductCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # 업데이트할 필드만 변경
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    # 업데이트 시간 갱신
    category.updated_datetime = utc_now()

    await session.commit()
    await session.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 삭제"""
    # Get category
    query = select(ProductCategory).where(
        and_(
            ProductCategory.id == category_id,
            ProductCategory.is_deleted == False,
        )
    )
    result = await session.stream(query)
    category = await result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Get related products
    query = select(Product).where(
        and_(
            Product.product_category_id == category_id,
            Product.is_deleted == False,
        )
    )
    result = await session.stream(query)
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

    await session.commit()
    return {"message": "Category and related products deleted successfully"}
