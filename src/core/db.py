from sqlalchemy import Engine, QueuePool, create_engine
from sqlmodel import Session

from core.config import settings

if settings.ENVIRONMENT == "local":
    engine = create_engine(
        "sqlite:///test.db", connect_args={"check_same_thread": False}
    )
else:
    dbschema = "db,public"

    engine = create_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        poolclass=QueuePool,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        connect_args={"options": f"-c search_path={dbschema}"},
    )


async def init_db(session: Session, engine: Engine) -> None:
    pass
