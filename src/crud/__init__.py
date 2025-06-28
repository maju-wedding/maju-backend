from models import ProductImage, Magazine, NewsItem, NewsCategory
from models.categories import Category
from models.checklists import Checklist
from models.product_ai_review import ProductAIReview
from models.product_categories import ProductCategory
from models.product_halls import ProductHall
from models.product_scores import ProductScore
from models.products import Product
from models.suggest_halls import RecommendedHall
from models.suggest_search_keywords import SuggestSearchKeyword
from models.user_spents import UserSpent
from models.user_wishlist import UserWishlist
from models.users import User
from .crud_categories import CRUDCategory
from .crud_checklist import CRUDChecklist
from .crud_magazine import CRUDMagazine
from .crud_news import CRUDNewsCategory, CRUDNewsItem
from .crud_product import CRUDProduct
from .crud_product_ai_review import CRUDProductAIReview
from .crud_product_category import CRUDProductCategory
from .crud_product_hall import CRUDProductHall
from .crud_product_image import CRUDProductImage
from .crud_product_score import CRUDProductScore
from .crud_suggest_halls import CRUDRecommendedHall
from .crud_suggest_search_keyword import CRUDSuggestSearchKeyword
from .crud_user import CRUDUser
from .crud_user_spents import CRUDUserSpent
from .crud_wishlist import CRUDUserWishlist

user = CRUDUser(User)
product = CRUDProduct(Product)
checklist = CRUDChecklist(Checklist)
category = CRUDCategory(Category)
product_hall = CRUDProductHall(ProductHall)
product_category = CRUDProductCategory(ProductCategory)
suggest_search_keyword = CRUDSuggestSearchKeyword(SuggestSearchKeyword)
user_wishlist = CRUDUserWishlist(UserWishlist)
product_ai_review = CRUDProductAIReview(ProductAIReview)
product_score = CRUDProductScore(ProductScore)
user_spent = CRUDUserSpent(UserSpent)
product_image = CRUDProductImage(ProductImage)
magazine = CRUDMagazine(Magazine)
news_category = CRUDNewsCategory(NewsCategory)
news_item = CRUDNewsItem(NewsItem)
recommended_hall = CRUDRecommendedHall(RecommendedHall)
