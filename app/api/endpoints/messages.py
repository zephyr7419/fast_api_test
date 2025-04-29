from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.schemas.message import MessageDevEUIResponse, AllDevEUIResponse, MessageQuery, PaginatedMessageResponse
from app.services.message_service import get_all_dev_euis, get_messages_by_dev_eui, get_all_devices_latest_data

# FastAPI의 APIRouter 사용
router = APIRouter()

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))


@router.get("/dev_euis", response_model=List[str])
async def list_all_dev_euis():
    """모든 고유한 devEUI 목록 반환"""
    return await get_all_dev_euis()


@router.get("/devices", response_model=List[AllDevEUIResponse])
async def list_all_devices_with_latest_data():
    """모든 디바이스의 최신 데이터 반환"""
    return await get_all_devices_latest_data()


@router.get("/dev_euis/{dev_eui}", response_model=Dict[str, Any])
async def get_device_info(
    dev_eui: str, 
    page: int = Query(1, description="페이지 번호"),
    page_size: int = Query(10, description="페이지당 항목 수"),
    start_date: str = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    """특정 devEUI를 가진 디바이스의 데이터 가져오기"""
    # MessageQuery 객체 생성
    query = MessageQuery(
        dev_eui=dev_eui,
        page=page,
        page_size=page_size,
        sort_by="content.publishedAt",  # MongoDB 필드 경로
        sort_order=-1
    )
    
    # start_date, end_date가 제공된 경우 설정 (한국 시간 기준)
    if start_date:
        try:
            # 한국 시간으로 시작일 설정 (00:00:00)
            start_dt = datetime.fromisoformat(start_date)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=KST)
            # UTC로 변환하여 저장
            query.start_date = start_dt.astimezone(timezone.utc)
        except ValueError:
            # 일반 날짜 형식으로 시도
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=KST)
            query.start_date = start_dt.astimezone(timezone.utc)
    
    if end_date:
        try:
            # 한국 시간으로 종료일 설정 (23:59:59)
            end_dt = datetime.fromisoformat(end_date)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=KST)
            # UTC로 변환하여 저장
            query.end_date = end_dt.astimezone(timezone.utc)
        except ValueError:
            # 일반 날짜 형식으로 시도
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=KST)
            query.end_date = end_dt.astimezone(timezone.utc)
    
    # 서비스 계층 함수 호출하여 데이터 가져오기
    result = await get_messages_by_dev_eui(query)
    
    # 응답의 날짜를 KST로 변환
    for item in result['items']:
        if hasattr(item, 'publishedAt') and item.publishedAt:
            # UTC로 저장된 날짜를 KST로 변환하여 표시
            if item.publishedAt.tzinfo is None:
                # timezone-naive 날짜는 UTC로 가정
                item.publishedAt = item.publishedAt.replace(tzinfo=timezone.utc)
            item.publishedAt = item.publishedAt.astimezone(KST)
    
    return result
