from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import create_engine
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from admin.setup import setup_admin
from api.v1.router import api_router
from core.config import settings
from core.db import async_engine
from core.exceptions import exception_handlers
from middleswares.logging import LoggingMiddleware
from utils.utils import custom_generate_unique_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(settings.DATABASE_URI.replace("+asyncpg", ""))
    SQLModel.metadata.create_all(engine)
    yield


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Serenade API",
        version="1.0.0",
        description="API description",
        routes=app.routes,
    )

    # Security schemes 설정
    openapi_schema["components"]["securitySchemes"] = {
        "User Login": {
            "type": "oauth2",
            "flows": {"password": {"tokenUrl": "/api/v1/auth/login", "scopes": {}}},
        },
        "Bearer Auth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


if settings.ENVIRONMENT != "production":
    sentry_sdk.init(
        dsn="https://a1a685906d17e8965e8b848f754d4cb1@o4509565448814592.ingest.us.sentry.io/4509565451304960",
        send_default_pii=True,
        environment=settings.ENVIRONMENT,
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    docs_url="/-/docs",
    redoc_url=None,
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)
app.openapi = custom_openapi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

setup_admin(app, async_engine)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount("/static", StaticFiles(directory="statics"), name="static")


@app.get("/")
async def read_root():
    return {"message": "Hello! Why do you come here?"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
