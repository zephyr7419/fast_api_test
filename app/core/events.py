import json
import logging
from typing import Callable

from fastapi import FastAPI

from app.db.base import engine, Base
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection
from app.db.session import get_db
from app.schemas.message import MessageCreate
from app.services.message_service import MessageService, create_message
from app.services.rabbitmq_service import RabbitMQService

logger = logging.getLogger("__name__")

async def process_message(payload: dict):
    """Process incoming messages from RabbitMQ."""
    async for db in get_db():
        MessageService()
        routing_key = payload.get("values", {}).get("devEUI", "default")

        message_data = MessageCreate(
            content = payload,
            routing_key = routing_key
        )
        await create_message(message_data)
        logger.info(f"Message saved to database: {payload}")

def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Create a function that handles app startup
    """
    async def start_app() -> None:
        await  connect_to_mongodb()

        # Set up RabbitMQ connection
        app.state.rabbitmq = RabbitMQService()
        await app.state.rabbitmq.connect()
        await app.state.rabbitmq.consume(process_message)

    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Create a function that handles app shutdown
    """
    async def stop_app() -> None:
        await app.state.rabbitmq.close()
        await close_mongodb_connection()
    return stop_app