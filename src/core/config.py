from pathlib import Path
from typing import Literal

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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ENVIRONMENT: Literal["test", "local", "staging", "production"]

    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET_ID: str = ""

    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET_ID: str = ""


class LocalSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.local")
    ENVIRONMENT: Literal["test", "local", "staging", "production"] = "local"

    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./test.db"


class TestSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.test")
    ENVIRONMENT: Literal["test", "local", "staging", "production"] = "test"


class StagingSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.staging")
    ENVIRONMENT: Literal["test", "local", "staging", "production"] = "staging"


class ProductionSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env.production")
    ENVIRONMENT: Literal["test", "local", "staging", "production"] = "production"

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""


def get_settings():
    env = Path(ROOT_DIR / ".env").read_text().strip()
    configs = {
        "local": LocalSettings,
        "test": TestSettings,
        "staging": StagingSettings,
        "production": ProductionSettings,
    }
    config_class = configs.get(env, LocalSettings)
    return config_class()


settings = get_settings()
