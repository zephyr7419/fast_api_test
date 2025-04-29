from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient


settings = get_settings()

# MongoDB 연결
mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongodb_database = mongodb_client[settings.MONGODB_DATABASE]

# SQLAlchemy 관련 코드는 현재 사용하지 않으므로 주석 처리
# engine = create_async_engine(
#     settings.SQLALCHEMY_DATABASE_URI, echo=True, future=True
# )
# 
# AsyncSessionLocal = sessionmaker(
#     autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
# )

Base = declarative_base()