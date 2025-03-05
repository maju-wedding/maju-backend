from fastapi import FastAPI, Request
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.sessions import SessionMiddleware

from admin.auth import AdminAuth
from admin.models import (
    UserAdmin,
    ChecklistAdmin,
    ChecklistCategoryAdmin,
)
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
    )

    # Setup middleware to inject session into request
    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.session = await anext(get_session())
        response = await call_next(request)
        return response

    # Register admin views
    admin.add_view(UserAdmin)
    admin.add_view(ChecklistCategoryAdmin)
    admin.add_view(ChecklistAdmin)
    # admin.add_view(UserWishlistAdmin)

    return admin
