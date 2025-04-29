from fastapi import APIRouter

from app.api.endpoints import messages

api_router = APIRouter()

# 현재 사용 중인 router 모듈 대신 FastAPI의 APIRouter 사용
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
