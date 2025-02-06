import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlmodel import Session, select
from starlette.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from core.config import settings
from core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing service")
    try:
        with Session(engine) as session:
            session.exec(select(1))
            await init_db(session, engine)
    except Exception as e:
        logger.error(e)
        raise e

    logger.info("Service finished initializing")

    yield

    logger.info("Service is shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
