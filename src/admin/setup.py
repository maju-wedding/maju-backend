from fastapi import FastAPI, Request
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.sessions import SessionMiddleware

from admin.auth import AdminAuth
from admin.models.categories import CategoryAdmin
from admin.models.checklists import ChecklistAdmin
from admin.models.product_ai_reviews import ProductAIReviewAdmin
from admin.models.product_categories import ProductCategoryAdmin
from admin.models.product_hall_venues import ProductHallVenueAdmin
from admin.models.product_halls import ProductHallAdmin
from admin.models.suggest_search_keywords import SuggestSearchKeywordAdmin
from admin.models.users import UserAdmin
from core.config import settings
from core.db import get_session


def setup_admin(app: FastAPI, engine: AsyncEngine):
    """Set up SQLAdmin with the FastAPI app."""
    # Add session middleware for authentication
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # Create authentication backend
    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

    # Create SQLAdmin instance
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title=f"{settings.PROJECT_NAME}",
        templates_dir="templates",
        favicon_url="/static/favicon.ico",
        logo_url="/static/logo.png",
        base_url="/-/admin",
    )

    # Setup middleware to inject session into request
    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.session = await anext(get_session())
        response = await call_next(request)
        return response

    # Register admin views
    # 유저
    admin.add_view(UserAdmin)
    # admin.add_view(UserWishlistAdmin)

    # 체크리스트
    admin.add_view(CategoryAdmin)
    admin.add_view(ChecklistAdmin)

    # 상품
    admin.add_view(ProductCategoryAdmin)
    admin.add_view(ProductAIReviewAdmin)
    admin.add_view(ProductHallAdmin)
    admin.add_view(ProductHallVenueAdmin)

    # 검색
    admin.add_view(SuggestSearchKeywordAdmin)
    return admin
