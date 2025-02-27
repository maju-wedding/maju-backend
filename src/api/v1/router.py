from fastapi import APIRouter

from api.v1.endpoints import users, auth, categories, checklists, products

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(checklists.router, prefix="/checklist", tags=["checklist"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
