from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from cruds.crud_categories import category_crud
from models.categories import CategoryUpdate, CategoryCreate, CategoryRead
from models.common import ResponseWithStatusMessage

router = APIRouter()


@router.get("/", response_model=list[CategoryRead])
async def read_categories(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    카테고리 목록 조회
    """
    categories = await category_crud.get_multi(
        session,
        limit=limit,
        offset=offset,
        return_as_model=True,
        schema_to_select=CategoryRead,
    )

    return categories.get("data", [])


@router.get("/{category_id}", response_model=CategoryRead)
async def read_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    카테고리 상세 조회
    """

    try:
        category = await category_crud.get(
            session, id=category_id, return_as_model=True, schema_to_select=CategoryRead
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("/", response_model=CategoryRead)
async def create_category(
    category_create: CategoryCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    카테고리 생성
    """
    try:
        category = await category_crud.create(
            session,
            category_create,
            return_as_model=True,
            schema_to_select=CategoryRead,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return category


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    카테고리 수정
    """

    try:
        category = await category_crud.update(
            session,
            category_update,
            id=category_id,
            return_as_model=True,
            schema_to_select=CategoryRead,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.delete("/{category_id}", response_model=ResponseWithStatusMessage)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    카테고리 삭제
    """

    try:
        is_deleted = await category_crud.delete(session, id=category_id)
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
