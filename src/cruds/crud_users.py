from fastcrud import FastCRUD

from models.users import User


class UserCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user_by_email(self, session, email) -> User:
        user = await self.get(session, email=email)
        return User(**user)


users_crud = UserCRUD(User)
