import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.api.api import api_router

settings = get_settings()

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS 미들웨어 설정 (config.py에서 메서드 사용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.get_cors_methods(),
    allow_headers=settings.get_cors_headers(),
)

# 이벤트 핸들러 등록
app.add_event_handler("startup", create_start_app_handler(app))
app.add_event_handler("shutdown", create_stop_app_handler(app))

# API 라우터 등록
app.include_router(api_router, prefix="/api")

@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
