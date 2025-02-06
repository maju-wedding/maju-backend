from sqlmodel import Session, select

from models.users import User, UserCreate, UserUpdateMe


async def create_user(*, session: Session, user_create: UserCreate) -> User:
    user = User(**user_create.dict())

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


async def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


async def get_user_by_id(*, session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


async def update_user(
    *, session: Session, user: User, user_update: UserUpdateMe
) -> User:
    update_data = user_update.model_dump(exclude_unset=True)

    user.sqlmodel_update(update_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


async def is_already_exist_nickname(*, session: Session, nickname: str) -> bool:
    statement = select(User).where(User.nickname == nickname)
    return session.exec(statement).first() is not None
