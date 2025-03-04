from fastapi import Request
from sqladmin.authentication import AuthenticationBackend

from core.security import verify_password
from cruds.users import users_crud
from models import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Get session from request state
        session = request.state.session

        # Find the user
        user = await users_crud.get(
            session, email=username, return_as_model=True, schema_to_select=User
        )

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
