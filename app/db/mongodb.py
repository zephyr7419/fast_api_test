import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class MongoDB:
    client = None
    db = None

async def connect_to_mongodb():
    """Connect to MongoDB database."""
    logger.info("Connecting to MongoDB...")
    MongoDB.client = AsyncIOMotorClient(settings.MONGODB_URL)
    MongoDB.db = MongoDB.client[settings.MONGODB_DATABASE]

    # 연결 확인
    try:
        # 서버 정보 요청
        await MongoDB.client.server_info()
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URL}")
    except ConnectionFailure:
        logger.error("Failed to connect to MongoDB.")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection."""
    if MongoDB.client:
        logger.info("Closing MongoDB connection...")
        MongoDB.client.close()
