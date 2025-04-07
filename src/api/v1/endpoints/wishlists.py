from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import get_current_user
from core.db import get_session
from cruds.user_wishlists import user_wishlists_crud
from models import User
from schemes.user_wishlist import (
    WishlistCreate,
    WishlistCreateInternal,
    WishlistUpdate,
    WishlistResponse,
    WishlistDetailResponse,
    WishlistListResponse,
)

router = APIRouter()


@router.get("", response_model=WishlistListResponse)
async def get_user_wishlists(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    현재 로그인한 사용자의 위시리스트를 조회합니다.
    """
    wishlists = await user_wishlists_crud.get_user_wishlists(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    total = await user_wishlists_crud.count_user_wishlists(
        db=db, user_id=current_user.id
    )

    return {
        "total": total,
        "items": wishlists,
    }


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    wishlist_in: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    현재 로그인한 사용자의 위시리스트에 제품을 추가합니다.
    """
    # 이미 위시리스트에 있는지 확인
    existing_wishlist = await user_wishlists_crud.get_wishlist_by_user_and_product(
        db=db, user_id=current_user.id, product_id=wishlist_in.product_id
    )

    if existing_wishlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 위시리스트에 추가된 상품입니다.",
        )

    # 위시리스트에 추가
    wishlist_data = WishlistCreateInternal(
        user_id=current_user.id,
        product_id=wishlist_in.product_id,
        memo=wishlist_in.memo,
    )

    return await user_wishlists_crud.create_wishlist(db=db, obj_in=wishlist_data)


@router.get("/{wishlist_id}", response_model=WishlistDetailResponse)
async def get_wishlist_detail(
    wishlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    위시리스트 항목의 세부 정보를 조회합니다.
    """
    wishlist = await user_wishlists_crud.get(db=db, id=wishlist_id)

    if not wishlist or wishlist.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위시리스트를 찾을 수 없습니다.",
        )

    # 현재 사용자의 위시리스트인지 확인
    if wishlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 위시리스트에 접근 권한이 없습니다.",
        )

    return wishlist


@router.patch("/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist(
    wishlist_id: int,
    wishlist_in: WishlistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    위시리스트 항목의 메모를 업데이트합니다.
    """
    wishlist = await user_wishlists_crud.get(db=db, id=wishlist_id)

    if not wishlist or wishlist.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위시리스트를 찾을 수 없습니다.",
        )

    # 현재 사용자의 위시리스트인지 확인
    if wishlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 위시리스트에 접근 권한이 없습니다.",
        )

    return await user_wishlists_crud.update_wishlist_memo(
        db=db, wishlist_id=wishlist_id, obj_in=wishlist_in
    )


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    wishlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    위시리스트에서 항목을 제거합니다.
    """
    wishlist = await user_wishlists_crud.get(db=db, id=wishlist_id)

    if not wishlist or wishlist.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위시리스트를 찾을 수 없습니다.",
        )

    # 현재 사용자의 위시리스트인지 확인
    if wishlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 위시리스트에 접근 권한이 없습니다.",
        )

    await user_wishlists_crud.soft_delete(db=db, wishlist_id=wishlist_id)
