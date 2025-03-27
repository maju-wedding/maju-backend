from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query, Path, Body
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_admin
from core.db import get_session
from cruds.product_categories import product_categories_crud
from models import User
from schemes.common import ResponseWithStatusMessage
from schemes.product_categories import (
    ProductCategoryRead,
    ProductCategoryCreate,
    ProductCategoryUpdate,
)

router = APIRouter()


@router.get("", response_model=list[ProductCategoryRead])
async def read_categories(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    카테고리 목록 조회
    """
    categories = await product_categories_crud.get_multi(
        session,
        is_deleted=False,
        limit=limit,
        offset=offset,
        return_as_model=True,
        schema_to_select=ProductCategoryRead,
        sort_columns=["order"],
        sort_orders=["asc"],
    )

    return categories.get("data", [])


@router.get("/{category_id}", response_model=ProductCategoryRead)
async def read_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """
    카테고리 상세 조회
    """

    category = await product_categories_crud.get(
        session,
        id=category_id,
        return_as_model=True,
        schema_to_select=ProductCategoryRead,
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("", response_model=ProductCategoryRead)
async def create_category(
    category_create: ProductCategoryCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """
    카테고리 생성
    """
    try:
        category = await product_categories_crud.create(
            session,
            category_create,
            return_as_model=True,
            schema_to_select=ProductCategoryRead,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return category


@router.put("/{category_id}", response_model=ProductCategoryRead)
async def update_category(
    category_id: int = Path(...),
    category_update: ProductCategoryUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """
    카테고리 수정
    """

    try:
        category = await product_categories_crud.update(
            session,
            category_update,
            id=category_id,
            return_as_model=True,
            schema_to_select=ProductCategoryRead,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.delete("/{category_id}", response_model=ResponseWithStatusMessage)
async def delete_category(
    category_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """
    카테고리 삭제
    """

    try:
        is_deleted = await product_categories_crud.delete(session, id=category_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Category not found")

    return {
        "status": "success" if is_deleted else "fail",
        "message": (
            "Category deleted successfully"
            if is_deleted
            else "Category deletion failed"
        ),
    }
