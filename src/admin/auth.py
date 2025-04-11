from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from core.security import verify_password
from models import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Get session from request state
        session = request.state.session

        # Find the user
        query = select(User).where(User.email == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_superuser:
            return False

        if not verify_password(password, user.hashed_password):
            return False

        # Save authentication in session
        request.session.update(
            {"admin_authenticated": True, "admin_user_id": str(user.id)}
        )
        return True

    async def logout(self, request: Request) -> bool:
        request.session.pop("admin_authenticated", None)
        request.session.pop("admin_user_id", None)
        return True

    async def authenticate(self, request: Request) -> bool | None:
        return request.session.get("admin_authenticated", False)
