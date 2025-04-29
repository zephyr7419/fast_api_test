from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field


# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))


class MessageBase(BaseModel):
    content: Dict[str, Any]
    routing_key: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str  # MongoDB ObjectId의 문자열 표현
    content: Dict[str, Any]  # JSON 객체로 반환
    routing_key: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageQuery(BaseModel):
    routing_key: Optional[str] = None
    dev_eui: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 10
    sort_by: str = "content.publishedAt"
    sort_order: int = -1

class PaginatedMessageResponse(BaseModel):
    items: List[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class MessageDevEUIResponse(BaseModel):
    battery: int = 0
    longitude: float = 0.0
    latitude: float = 0.0
    publishedAt: datetime
    
    # 클라이언트에게 보여줄 때 KST로 변환된 날짜
    published_at_kst: str = Field(None)
    
    def __init__(self, **data):
        super().__init__(**data)
        # publishedAt이 있으면 KST로 변환해서 published_at_kst 필드 설정
        if hasattr(self, 'publishedAt') and self.publishedAt:
            if self.publishedAt.tzinfo is None:
                # timezone-naive 날짜는 UTC로 가정
                self.publishedAt = self.publishedAt.replace(tzinfo=timezone.utc)
            kst_time = self.publishedAt.astimezone(KST)
            self.published_at_kst = kst_time.strftime('%Y-%m-%d %H:%M:%S KST')

class AllDevEUIResponse(BaseModel):
    dev_eui: str
    device_name: str
    company: str
    sensor_type: str = ""
    battery: int = 0
    longitude: float = 0.0
    latitude: float = 0.0
    publishedAt: Optional[datetime] = None
    
    # 클라이언트에게 보여줄 때 KST로 변환된 날짜
    published_at_kst: str = Field(None)
    
    def __init__(self, **data):
        super().__init__(**data)
        # publishedAt이 있으면 KST로 변환해서 published_at_kst 필드 설정
        if hasattr(self, 'publishedAt') and self.publishedAt:
            if self.publishedAt.tzinfo is None:
                # timezone-naive 날짜는 UTC로 가정
                self.publishedAt = self.publishedAt.replace(tzinfo=timezone.utc)
            kst_time = self.publishedAt.astimezone(KST)
            self.published_at_kst = kst_time.strftime('%Y-%m-%d %H:%M:%S KST')
