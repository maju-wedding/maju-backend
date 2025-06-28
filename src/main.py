from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from admin.setup import setup_admin
from api.v1.router import api_router
from core.config import settings
from core.db import async_engine, check_db_connection, close_db_connections
from core.exceptions import exception_handlers
from core.logging import setup_logging
from middleswares.logging import LoggingMiddleware
from utils.utils import custom_generate_unique_id

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # engine = create_engine(settings.DATABASE_URI.replace("+asyncpg", ""))
    # SQLModel.metadata.create_all(engine)

    try:
        connection_healthy = await check_db_connection()
        if connection_healthy:
            print("✅ Database connection pool warmed up")
        else:
            print("⚠️ Database connection test failed")
    except Exception as e:
        print(f"❌ Database warmup failed: {e}")

    print("🎉 Application startup completed")

    yield  # 애플리케이션 실행

    # 종료 시 정리
    print("🛑 Shutting down application...")
    try:
        await close_db_connections()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")

    print("👋 Application shutdown completed")


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
        traces_sample_rate=0.1,
        sample_rate=1,
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


@app.get("/", include_in_schema=False)
async def read_root():
    return {"message": "Hello! Why do you come here?"}


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}
