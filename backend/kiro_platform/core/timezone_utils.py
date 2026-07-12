from datetime import datetime, timezone, timedelta


def get_beijing_time() -> datetime:
    """获取北京时间（UTC+8）"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz)


def get_utc_time() -> datetime:
    """获取UTC时间"""
    return datetime.now(timezone.utc)