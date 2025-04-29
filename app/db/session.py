from typing import AsyncGenerator

from app.db.mongodb import MongoDB

async def get_db() -> AsyncGenerator:
    """Dependency for getting MongoDB database session"""
    if MongoDB.db is None:
        yield None
    else:
        yield MongoDB.db