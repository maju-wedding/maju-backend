from fastcrud import FastCRUD

from models.users import User


class UserCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


users_crud = UserCRUD(User)
