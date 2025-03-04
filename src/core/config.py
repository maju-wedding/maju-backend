import os
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Reborn"

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 3  # 3 days
    ENVIRONMENT: Literal["test", "local", "production"]

    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET_ID: str = ""

    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET_ID: str = ""


class LocalSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.local")
    ENVIRONMENT: Literal["test", "local", "production"] = "local"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "reborn"
    POSTGRES_PASSWORD: str = "reborn"
    POSTGRES_DB: str = "reborn"

    @computed_field
    def DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class TestSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.test")
    ENVIRONMENT: Literal["test", "local", "production"] = "test"

    DATABASE_URI: str = "sqlite+aiosqlite:///:memory:"


class ProductionSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.prod")
    ENVIRONMENT: Literal["test", "local", "staging", "production"] = "production"

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    @computed_field
    def DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


def get_settings():
    configs = {
        "local": LocalSettings,
        "test": TestSettings,
        "production": ProductionSettings,
    }
    config_class = configs.get(os.getenv("ENVIRONMENT"), LocalSettings)
    return config_class()


settings = get_settings()
