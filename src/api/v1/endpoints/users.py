from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from crud import user as crud_user
from crud import user_wishlist as crud_wishlist
from models import User
from schemes.common import ResponseWithStatusMessage
from schemes.user_wishlist import WishlistCreate
from schemes.users import UserUpdate, UserRead

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserRead)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """내 정보 조회"""
    return current_user


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 정보 업데이트"""
    updated_user = await crud_user.update(
        db=session, db_obj=current_user, obj_in=user_update
    )
    return updated_user


@router.delete(
    "/me", status_code=status.HTTP_200_OK, response_model=ResponseWithStatusMessage
)
async def delete_user_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 계정 삭제"""
    await crud_user.soft_delete(db=session, id=current_user.id)
    return ResponseWithStatusMessage(
        status="success",
        message="User deleted successfully",
    )


@router.get("/me/wishlist", status_code=status.HTTP_200_OK, response_model=list)
async def list_wishlist(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 위시리스트 조회"""
    wishlists = await crud_wishlist.get_by_user(db=session, user_id=current_user.id)
    return wishlists


@router.post("/me/wishlist", status_code=status.HTTP_201_CREATED, response_model=dict)
async def add_to_wishlist(
    wishlist_create: WishlistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """위시리스트 추가"""
    # 상품 존재 확인
    from crud import product as crud_product

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
    "/me/wishlist/{product_id}",
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


@router.get("", status_code=status.HTTP_200_OK, response_model=list[User])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """관리자용 사용자 목록 조회"""
    users = await crud_user.get_multi(db=session, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """사용자 상세 정보 조회"""
    user = await crud_user.get(db=session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
