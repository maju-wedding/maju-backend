from fastapi import APIRouter, Query, Depends, HTTPException
from fastcrud import JoinConfig
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from cruds.crud_products import product_crud
from models import ProductHall, Product, Category

router = APIRouter()

product_detail_join_config = [
    JoinConfig(
        model=Category,
        join_on=Product.category_id == Category.id,
        join_type="inner",
        join_prefix="category_",
    ),
    JoinConfig(
        model=ProductHall,
        join_on=Product.id == ProductHall.product_id,
        join_type="left",
        join_prefix="hall_",
    ),
]


@router.get("/")
async def list_products(
    category_id: int = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = {}
    if category_id:
        query["category_id"] = category_id

    products = await product_crud.get_multi_joined(
        session,
        limit=limit,
        offset=offset,
        joins_config=product_detail_join_config,
        nest_joins=True,
        **query,
    )

    return products


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    product = await product_crud.get_joined(
        session,
        joins_config=product_detail_join_config,
        nest_joins=True,
        id=product_id,
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
