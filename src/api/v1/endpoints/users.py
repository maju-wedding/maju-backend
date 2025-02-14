from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from cruds.products import products_crud
from cruds.user_wishlists import user_wishlists_crud
from cruds.users import users_crud
from models.user_wishlist import WishlistCreate, WishlistCreateInternal, UserWishlist
from models.users import UserUpdate, User, UserRead

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """
    내 정보 조회
    """
    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(current_user),
    }


@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_user_me(
    user_update: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    내 정보 업데이트
    """
    updated_user = await users_crud.update(
        session, user_update.model_dump(exclude_unset=True), id=current_user.id
    )

    return {
        "success": True,
        "message": "",
        "data": jsonable_encoder(updated_user),
    }


@router.get("/me/wishlist")
async def list_wishlist(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    내 위시리스트 조회
    """
    wishlists = await user_wishlists_crud.get_multi(
        session,
        user_id=current_user.id,
    )
    return wishlists


@router.post("/me/wishlist")
async def add_to_wishlist(
    wishlist_create: WishlistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Check if product exists
    product = await products_crud.get(session, id=wishlist_create.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_wishlist = await user_wishlists_crud.get(
        session,
        user_id=current_user.id,
        product_id=wishlist_create.product_id,
    )

    if existing_wishlist:
        raise HTTPException(status_code=400, detail="Product already in wishlist")

    # Create wishlist
    wishlist = await user_wishlists_crud.create(
        session,
        WishlistCreateInternal(
            user_id=current_user.id, product_id=wishlist_create.product_id
        ),
    )
    return wishlist


@router.delete("/me/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    wishlist = await user_wishlists_crud.get(
        session,
        user_id=current_user.id,
        product_id=product_id,
        return_as_model=True,
        schema_to_select=UserWishlist,
    )

    if not wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    await user_wishlists_crud.delete(session, id=wishlist.id)
    return {"success": True, "message": "", "data": None}


@router.get("/", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """관리자용 사용자 목록 조회"""
    users = await users_crud.get_multi(
        session,
        offset=offset,
        limit=limit,
        is_active=True,
        is_deleted=False,
    )

    return users.get("data", [])


@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: UUID = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """사용자 삭제 (soft delete)"""
    user = await users_crud.get(session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot delete superuser")

    await users_crud.delete(session, id=user_id)

    return {"success": True, "message": "", "data": None}
