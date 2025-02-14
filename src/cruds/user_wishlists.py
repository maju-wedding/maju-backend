from fastcrud import FastCRUD

from models import UserWishlist


class UserWishlistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


user_wishlists_crud = UserWishlistCRUD(UserWishlist)
