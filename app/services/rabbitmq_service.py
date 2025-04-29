import json
import logging
from typing import Callable, Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        """Establish connection to RabbitMQ server."""
        logger.info("Connecting to RabbitMQ server...")
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()

        # Declare queue
        self.exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        self.queue = await self.channel.declare_queue(
            settings.RABBITMQ_QUEUE,
            durable=True
        )

        await self.queue.bind(
            exchange=self.exchange,
            routing_key=settings.RABBITMQ_ROUTING_KEY
        )

        logger.info(f"Connected to RabbitMQ, queue: {settings.RABBITMQ_QUEUE}")

    async def close(self):
        """Close connection to RabbitMQ server."""
        if self.connection:
            await self.connection.close()

    async def consume(self, callback: Callable[[dict], Any]):
        """Start consuming messages"""
        async def process_message(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    payload = json.loads(message.body.decode())
                    logger.info(f"Received message: {payload}")
                    await callback(payload)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await self.queue.consume(process_message)
        logger.info("Started consuming messages.")


