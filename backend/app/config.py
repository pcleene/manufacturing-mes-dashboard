"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # MongoDB
    mongodb_uri: str = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>"
    mongodb_database: str = "OEMPartner_mes_demo"

    # Application
    app_env: str = "development"
    app_debug: bool = True

    # Timezone
    timezone: str = "Asia/Kuala_Lumpur"

    # API
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
