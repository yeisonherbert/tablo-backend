"""Configuración central de la aplicación.

Las variables se leen desde el entorno (o de un archivo .env en desarrollo).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Base de datos (PostgreSQL 18 / asyncpg) ---
    DB_HOST: str = "postgres-dev.cb4oayqkid8w.us-east-2.rds.amazonaws.com"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Pass123--"
    DB_NAME: str = "postgres"
    DB_ECHO: bool = False

    # --- JWT ---
    JWT_SECRET: str = "cambia-esto-en-produccion-por-un-secreto-largo-y-aleatorio"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

    # --- App ---
    APP_NAME: str = "Tablo API"
    AVATAR_BASE_URL: str = "https://i.pravatar.cc/300"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
