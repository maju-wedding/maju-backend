from sqladmin import ModelView

from models import UserWishlist


class UserWishlistAdmin(ModelView, model=UserWishlist):
    name = "위시리스트"
    name_plural = "위시리스트 목록"
    icon = "fa-solid fa-heart"
    category = "유저 관리"

    column_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    column_labels = {
        UserWishlist.id: "위시리스트 ID",
        UserWishlist.user_id: "사용자 ID",
        UserWishlist.product_id: "상품 ID",
        UserWishlist.created_datetime: "생성일시",
    }

    column_details_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    column_formatters = {
        UserWishlist.created_datetime: lambda m, a: (
            m.created_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if m.created_datetime
            else ""
        ),
    }

    column_sortable_list = [
        UserWishlist.id,
        UserWishlist.user_id,
        UserWishlist.product_id,
        UserWishlist.created_datetime,
    ]

    can_create = True
    can_edit = False  # Wishlists are typically not edited
    can_delete = True
    can_view_details = True
