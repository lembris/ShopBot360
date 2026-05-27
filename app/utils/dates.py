from datetime import datetime, timedelta

import pytz


def get_shop_tz(timezone_name: str):
    return pytz.timezone(timezone_name)


def today_range(timezone_name: str) -> tuple[datetime, datetime]:
    tz = get_shop_tz(timezone_name)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def week_range(timezone_name: str) -> tuple[datetime, datetime]:
    tz = get_shop_tz(timezone_name)
    now = datetime.now(tz)
    start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end
