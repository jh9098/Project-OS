from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    APP_ENV: str = 'development'
    APP_NAME: str = 'Project OS API'
    API_V1_PREFIX: str = '/api/v1'
    SECRET_KEY: str = 'change-this-secret-key'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = 'sqlite:///./app.db'
    CORS_ORIGINS: List[str] | str = ['http://localhost:3000']
    ADMIN_USERNAME: str = 'admin'
    ADMIN_PASSWORD: str = 'admin1234'

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
