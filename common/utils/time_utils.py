from datetime import datetime

def create_from_second_now() -> datetime:
    return datetime.now().replace(microsecond=0)

def create_from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp)

def create_from_second_now_to_int() -> int:
    return int(create_from_second_now().timestamp())

def create_from_timestamp_to_int(datatime: datetime) -> int:
    return int(datatime.timestamp())