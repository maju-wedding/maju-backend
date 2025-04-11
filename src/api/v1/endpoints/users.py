from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_
from starlette import status

from api.v1.deps import get_current_user, get_current_admin
from core.db import get_session
from models import User, Product, UserWishlist
from schemes.common import ResponseWithStatusMessage
from schemes.user_wishlist import WishlistCreate
from schemes.users import UserUpdate, UserRead, UserCreate
from utils.utils import utc_now

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
    query = select(User).where(
        and_(
            User.id == current_user.id,
            User.is_active == True,
            User.is_deleted == False,
        )
    )
    result = await session.stream(query)
    db_user = await result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.sqlmodel_update(
        user_update.model_dump(exclude_unset=True),
    )

    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.delete(
    "/me", status_code=status.HTTP_200_OK, response_model=ResponseWithStatusMessage
)
async def delete_user_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """내 계정 삭제"""
    query = select(User).where(
        User.id == current_user.id, User.is_active == True, User.is_deleted == False
    )
    result = await session.execute(query)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = False
    db_user.is_deleted = True
    db_user.deleted_datetime = utc_now()

    await session.commit()
    return ResponseWithStatusMessage(
        status="success",
        message="User deleted successfully",
    )


@router.get(
    "/me/wishlist", status_code=status.HTTP_200_OK, response_model=list[UserWishlist]
)
async def list_wishlist(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    내 위시리스트 조회
    """
    query = select(UserWishlist).where(
        UserWishlist.user_id == current_user.id,
        UserWishlist.is_deleted == False,
    )
    result = await session.execute(query)
    wishlists = result.scalars().all()
    return wishlists


@router.post(
    "/me/wishlist", status_code=status.HTTP_201_CREATED, response_model=UserWishlist
)
async def add_to_wishlist(
    wishlist_create: WishlistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Check if product exists
    query = select(Product).where(
        Product.id == wishlist_create.product_id, Product.is_deleted == False
    )
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = select(UserWishlist).where(
        UserWishlist.user_id == current_user.id,
        UserWishlist.product_id == wishlist_create.product_id,
        UserWishlist.is_deleted == False,
    )
    result = await session.execute(query)
    existing_wishlist = result.scalar_one_or_none()

    if existing_wishlist:
        raise HTTPException(status_code=400, detail="Product already in wishlist")

    # Create wishlist
    wishlist = UserWishlist(
        user_id=current_user.id,
        product_id=wishlist_create.product_id,
    )
    session.add(wishlist)
    await session.commit()
    await session.refresh(wishlist)
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
    query = select(UserWishlist).where(
        UserWishlist.user_id == current_user.id,
        UserWishlist.product_id == product_id,
        UserWishlist.is_deleted == False,
    )
    result = await session.execute(query)
    wishlist = result.scalar_one_or_none()

    if not wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    wishlist.is_deleted = True
    await session.commit()

    return ResponseWithStatusMessage(
        status="success",
        message="Wishlist deleted successfully",
    )


@router.get("", status_code=status.HTTP_200_OK, response_model=list[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """관리자용 사용자 목록 조회"""
    query = (
        select(User)
        .where(User.is_active == True, User.is_deleted == False)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(query)
    users = result.scalars().all()
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """사용자 상세 정보 조회"""
    query = select(User).where(
        User.id == user_id, User.is_active == True, User.is_deleted == False
    )
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("")
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    db_user = User(**user.model_dump())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)

    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(db_user)
    await session.commit()
    return {"message": "User deleted successfully"}
