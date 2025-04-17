from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user
from core.db import get_session
from crud import product as crud_product
from crud import user_wishlist as crud_wishlist
from models import User
from schemes.common import ResponseWithStatusMessage
from schemes.user_wishlist import WishlistCreate

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK, response_model=list)
async def list_wishlist(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 위시리스트 조회"""
    wishlists = await crud_wishlist.get_by_user(db=session, user_id=current_user.id)
    return wishlists


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
async def add_to_wishlist(
    wishlist_create: WishlistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """위시리스트 추가"""
    # 상품 존재 확인

    product = await crud_product.get(db=session, id=wishlist_create.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 이미 위시리스트에 있는지 확인
    existing_wishlist = await crud_wishlist.get_by_user_and_product(
        db=session, user_id=current_user.id, product_id=wishlist_create.product_id
    )

    if existing_wishlist:
        raise HTTPException(status_code=400, detail="Product already in wishlist")

    # 위시리스트 생성
    wishlist = await crud_wishlist.create(
        db=session,
        obj_in={
            "user_id": current_user.id,
            "product_id": wishlist_create.product_id,
            "memo": wishlist_create.memo,
        },
    )
    return wishlist


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ResponseWithStatusMessage,
)
async def remove_from_wishlist(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """위시리스트 삭제"""
    wishlist = await crud_wishlist.get_by_user_and_product(
        db=session, user_id=current_user.id, product_id=product_id
    )

    if not wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    await crud_wishlist.soft_delete(db=session, id=wishlist.id)

    return ResponseWithStatusMessage(
        status="success",
        message="Wishlist deleted successfully",
    )
