from functools import lru_cache
from typing import List, Union

from pydantic.v1 import BaseSettings, validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Message processor"

    # Mongo
    MONGODB_URL: str
    MONGODB_DATABASE: str

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: str = None

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_VIRTUAL_HOST: str
    RABBITMQ_QUEUE: str
    RABBITMQ_EXCHANGE: str
    RABBITMQ_ROUTING_KEY: str
    
    # CORS 설정 - 문자열로 받은 다음 검증 시 변환
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v, values):
        if v is None or v == "":
            return f"postgresql+asyncpg://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_SERVER']}:{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"
        return v

    def get_cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
    def get_cors_methods(self) -> List[str]:
        if self.CORS_ALLOW_METHODS == "*":
            return ["*"]
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",") if method.strip()]
        
    def get_cors_headers(self) -> List[str]:
        if self.CORS_ALLOW_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",") if header.strip()]

@lru_cache
def get_settings():
    return Settings()