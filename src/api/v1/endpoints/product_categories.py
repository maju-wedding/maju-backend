from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from crud import product_category as crud_category
from schemes.product_categories import ProductCategoryCreate, ProductCategoryUpdate

router = APIRouter()


@router.get("")
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 목록 조회"""
    categories = await crud_category.get_all_active(db=session, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}")
async def get_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 상세 조회"""
    category = await crud_category.get(db=session, id=category_id)

    if not category or category.is_deleted:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("")
async def create_category(
    category_create: ProductCategoryCreate,
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 생성"""
    # Create category with automatic order increment
    category = await crud_category.create_with_order(db=session, obj_in=category_create)
    return category


@router.put("/{category_id}")
async def update_category(
    category_id: int = Path(...),
    category_update: ProductCategoryUpdate = None,
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 수정"""
    category = await crud_category.get(db=session, id=category_id)

    if not category or category.is_deleted:
        raise HTTPException(status_code=404, detail="Category not found")

    # 업데이트
    updated_category = await crud_category.update(
        db=session, db_obj=category, obj_in=category_update
    )

    return updated_category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """상품 카테고리 삭제"""
    category = await crud_category.get(db=session, id=category_id)

    if not category or category.is_deleted:
        raise HTTPException(status_code=404, detail="Category not found")

    # 카테고리와 관련 상품 삭제 처리
    await crud_category.soft_delete_with_products(db=session, category_id=category_id)

    return {"message": "Category and related products deleted successfully"}
