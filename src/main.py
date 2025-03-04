import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from admin import setup_admin
from api.v1.router import api_router
from core.config import settings
from core.db import async_engine
from core.exceptions import exception_handlers
from middleswares.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service finished initializing")
    yield
    logger.info("Service is shutting down")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API description",
        routes=app.routes,
    )

    # Security schemes 설정
    openapi_schema["components"]["securitySchemes"] = {
        "User Login": {
            "type": "oauth2",
            "flows": {"password": {"tokenUrl": "api/v1/auth/login", "scopes": {}}},
        },
        "Bearer Auth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
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
