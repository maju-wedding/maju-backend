from .categories import Category
from .checklists import Checklist
from .magazines import Magazine
from .news import NewsItem, NewsCategory
from .product_ai_review import ProductAIReview
from .product_blogs import ProductBlog
from .product_categories import ProductCategory
from .product_halls import ProductHall
from .product_images import ProductImage
from .product_scores import ProductScore
from .product_studio_packages import ProductStudioPackage
from .product_studios import ProductStudio
from .products import Product
from .suggest_halls import RecommendedHall
from .suggest_search_keywords import SuggestSearchKeyword
from .user_spents import UserSpent
from .user_wishlist import UserWishlist
from .users import User

all_models = [
    User,
    UserWishlist,
    UserSpent,
    SuggestSearchKeyword,
    Category,
    Checklist,
    Product,
    ProductCategory,
    ProductImage,
    ProductAIReview,
    ProductScore,
    ProductHall,
    ProductStudio,
    ProductStudioPackage,
    ProductBlog,
    NewsItem,
    NewsCategory,
    Magazine,
    RecommendedHall,
]

__all__ = [m.__name__ for m in all_models]

for model in all_models:
    if hasattr(model, "__tablename__"):
        table = getattr(model, "__table__", None)
