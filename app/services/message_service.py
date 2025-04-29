import datetime
import json
import re
from app.schemas.message import AllDevEUIResponse
import logging

from app.db.mongodb import MongoDB, logger
from app.schemas.message import MessageResponse, MessageQuery, MessageDevEUIResponse


async def create_message(message_data):
    """Create a new message in the database"""
    collection = MongoDB.db.messages

    # 내용을 객체로 변환 (문자열인 경우)
    if isinstance(message_data.content, str):
        content_data = json.loads(message_data.content)
    else:
        content_data = message_data.content.copy()

    # 날짜 정규식 패턴 - "2025-04-28T02:44:39.559014059Z" 같은 형식

    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$')

    # 날짜 필드 변환 함수
    def convert_date_fields(obj):
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                # publishedAt, time, nsTime 등의 필드에 대해
                if key in ["publishedAt", "time", "nsTime"] and isinstance(value, str):
                    if date_pattern.match(value):
                        try:
                            # 날짜 부분과 시간 부분 추출
                            date_part = value[:10]  # "2025-04-28"
                            time_part = value[11:19]  # "02:44:39"

                            # 날짜 객체 생성
                            date_obj = datetime.datetime.strptime(
                                f"{date_part} {time_part}",
                                "%Y-%m-%d %H:%M:%S"
                            )

                            # MongoDB에서는 aware datetime을 권장
                            date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
                            obj[key] = date_obj
                        except Exception as e:
                            print(f"날짜 변환 실패 ({key}={value}): {e}")

                # 재귀 처리
                elif isinstance(value, dict) or isinstance(value, list):
                    convert_date_fields(value)

        elif isinstance(obj, list):
            for item in obj:
                convert_date_fields(item)

    # 날짜 필드 변환
    try:
        convert_date_fields(content_data)
    except Exception as e:
        print(f"전체 변환 실패: {e}")

    message_dict = {
        "content": content_data,
        "routing_key": message_data.routing_key,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }

    # MongoDB에 저장
    result = await collection.insert_one(message_dict)
    created_message = await collection.find_one({"_id": result.inserted_id})

    # 응답 데이터 준비
    response_data = {
        "id": str(created_message.pop("_id")),
        "content": created_message.get("content"),
        "routing_key": created_message.get("routing_key"),
        "created_at": created_message.get("created_at")
    }

    return MessageResponse(**response_data)

async def get_all_dev_euis():
    """Get all device EUI IDs"""
    collection = MongoDB.db.messages

    dev_euis = await collection.distinct("content.values.devEUI")

    dev_euis.sort()
    return dev_euis

async def get_all_devices_latest_data():
    """Get the latest data for all devices"""
    collection = MongoDB.db.messages

    # MongoDB Aggregation 파이프라인
    pipeline = [
        # content.values.devEUI 필드가 존재하는 문서만 필터링
        {"$match": {"content.values.devEUI": {"$exists": True}}},

        # content.publishedAt 기준으로 정렬 (최신순)
        {"$sort": {"content.values.publishedAt": -1}},

        # devEUI 기준으로 그룹화하고 첫 번째 문서(최신)만 유지
        {"$group": {
            "_id": "$content.values.devEUI",
            "doc": {"$first": "$$ROOT"}
        }},

        # 원래 문서 구조로 변환
        {"$replaceRoot": {"newRoot": "$doc"}}
    ]

    cursor = collection.aggregate(pipeline)

    result = []

    async for doc in cursor:
        try:
            content = doc.get("content", {})
            values = content.get("values", {})

            # 요구되는 필드 추출 시 None 값에 대한 처리 추가
            dev_eui = values.get("devEUI", "")

            # 필수 필드인 dev_eui가 비어있으면 건너뛰기
            if not dev_eui:
                continue

            # AllDevEUIResponse 객체 생성
            device_info = content.get("uplinkEvent", {}).get("deviceInfo", {})
            tags = device_info.get("tags", {})

            logger.info(f"dev_eui: {dev_eui}")
            logger.info(f"device_info: {device_info}")
            logger.info(f"values: {values}")
            logger.info(f"tags: {tags}")

            device_data = {
                "dev_eui": dev_eui,
                "device_name": device_info.get("deviceName", ""),
                "company": tags.get("company", ""),
                "sensor_type": tags.get("type", ""),
                "battery": values.get("batteryLevel", 0),
                "longitude": values.get("longitude", 0.0),
                "latitude": values.get("latitude", 0.0),
                "publishedAt": values.get("publishedAt", None)  # None 가능
            }

            # 유효한 데이터만 추가
            device = AllDevEUIResponse(**device_data)
            result.append(device)
        except Exception as e:
            logging.error(f"데이터 변환 중 오류 (device: {values.get('devEUI', 'unknown')}): {e}")
            continue

    return result

async def get_messages(query: MessageQuery):
    """Get messages from MongoDB"""
    collection = MongoDB.db.messages

    filter_condition = {}

    if query.routing_key:
        filter_condition["routing_key"] = query.routing_key

    if query.dev_eui:
        filter_condition["content.values.devEUI"] = query.dev_eui

    date_filter = {}
    if query.start_date:
        date_filter["$gte"] = query.start_date
    if query.end_date:
        date_filter["$lte"] = query.end_date

    if date_filter:
        filter_condition["content.publishedAt"] = date_filter

    # 정렬 조건
    sort_condition = [(query.sort_by, query.sort_order)]

    # 페이지네이션 계산
    skip = (query.page - 1) * query.page_size

    # 전체 문서 수 계산
    total = await collection.count_documents(filter_condition)

    # 문서 조회
    cursor = collection.find(filter_condition)
    cursor.sort(sort_condition)
    cursor.skip(skip)
    cursor.limit(query.page_size)

    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(MessageResponse(**doc))

    # 페이지네이션 응답 구성
    return {
        "items": items,
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
        "total_pages": (total + query.page_size - 1) // query.page_size
    }

async def get_messages_by_dev_eui(query: MessageQuery):
    """
    특정 필드만 추출하여 메시지 조회
    """
    collection = MongoDB.db.messages

    # 필터 조건 구성
    filter_condition = {}

    # 라우팅 키로 필터링
    if query.routing_key:
        filter_condition["routing_key"] = query.routing_key

    # devEUI로 필터링
    if query.dev_eui:
        filter_condition["content.values.devEUI"] = query.dev_eui

    # 날짜 범위로 필터링
    date_filter = {}
    if query.start_date:
        date_filter["$gte"] = query.start_date
    if query.end_date:
        date_filter["$lte"] = query.end_date

    if date_filter:
        filter_condition["content.values.publishedAt"] = date_filter

    # 정렬 조건
    sort_condition = [(query.sort_by, query.sort_order)]

    # 페이지네이션 계산
    skip = (query.page - 1) * query.page_size

    # 전체 문서 수 계산
    total = await collection.count_documents(filter_condition)

    # 문서 조회 (필요한 필드만 선택)
    cursor = collection.find(filter_condition)
    cursor.sort(sort_condition)
    cursor.skip(skip)
    cursor.limit(query.page_size)

    items = []
    async for doc in cursor:
        try:
            # 필요한 필드 추출
            content = doc.get("content", {})
            values = content.get("values", {})

            logger.info(f"values: {values}")

            # MessageDevEUIResponse 객체 생성
            message_data = {
                "battery": values.get("batteryLevel", 0),
                "longitude": values.get("longitude", 0.0),
                "latitude": values.get("latitude", 0.0),
                "publishedAt": values.get("publishedAt", datetime.datetime.now())
            }

            items.append(MessageDevEUIResponse(**message_data))
        except Exception as e:
            # 예외 처리 (필드가 없는 경우 등)
            print(f"데이터 변환 중 오류: {e}")
            continue

    # 페이지네이션 응답 구성
    return {
        "items": items,
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
        "total_pages": (total + query.page_size - 1) // query.page_size
    }

class MessageService:
    pass