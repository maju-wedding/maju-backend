from .product_categories import ProductCategory
from .checklist import UserChecklist, SuggestChecklist
from .product_halls import ProductHall
from .products import Product
from .user_wishlist import UserWishlist
from .users import User

all_models = [
    User,
    ProductCategory,
    UserChecklist,
    SuggestChecklist,
    Product,
    ProductHall,
    UserWishlist,
]

__all__ = [m.__name__ for m in all_models]

for model in all_models:
    if hasattr(model, "__tablename__"):
        table = getattr(model, "__table__", None)
