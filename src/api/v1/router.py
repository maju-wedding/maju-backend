from fastapi import APIRouter

from api.v1.endpoints import (
    users,
    auth,
    product_categories,
    checklists,
    products,
    checklist_categories,
    suggest_search_keywords,
    product_halls,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    checklist_categories.router,
    prefix="/checklist_categories",
    tags=["checklist_categories"],
)
api_router.include_router(checklists.router, prefix="/checklists", tags=["checklists"])
api_router.include_router(
    product_categories.router, prefix="/product_categories", tags=["product_categories"]
)
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(
    product_halls.router, prefix="/wedding-halls", tags=["wedding-halls"]
)
api_router.include_router(
    suggest_search_keywords.router, prefix="/suggest-search-keywords", tags=["suggest"]
)
