from sqlalchemy import Column, Integer, Text, String, DateTime, func

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    routing_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())