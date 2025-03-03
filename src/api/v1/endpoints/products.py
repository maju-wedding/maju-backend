from fastapi import APIRouter, Query, Depends, HTTPException
from fastcrud import JoinConfig
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from cruds.products import products_crud, products_halls_crud
from models import ProductHall, Product, ProductCategory
from schemes.product_halls import ProductHallCreate, ProductHallCreateInternal

router = APIRouter()

product_detail_join_config = [
    JoinConfig(
        model=ProductCategory,
        join_on=Product.product_category_id == ProductCategory.id,
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


@router.get("")
async def list_products(
    category_id: int = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = {}
    if category_id:
        query["category_id"] = category_id

    products = await products_crud.get_multi_joined(
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
    product = await products_crud.get_joined(
        session,
        joins_config=product_detail_join_config,
        nest_joins=True,
        id=product_id,
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/wedding-halls")
async def create_wedding_halls(
    product_hall_create: ProductHallCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        product = await products_crud.create(
            session,
            product_hall_create,
            commit=False,
        )

        await session.flush()

        product_hall = await products_halls_crud.create(
            session,
            ProductHallCreateInternal(
                product_id=product.id,
                **product_hall_create.model_dump(),
            ),
            commit=False,
        )

        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return product_hall
