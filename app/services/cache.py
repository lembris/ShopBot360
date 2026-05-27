import json
from typing import Any

from app.core.constants import REPORT_CACHE_TTL_SECONDS
from app.services.redis import get_redis


class CacheService:
    async def get(self, key: str) -> Any | None:
        r = await get_redis()
        raw = await r.get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: Any, ttl: int = REPORT_CACHE_TTL_SECONDS) -> None:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        r = await get_redis()
        await r.delete(key)

    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        r = await get_redis()
        return bool(await r.set(f"lock:{key}", "1", nx=True, ex=ttl))

    async def release_lock(self, key: str) -> None:
        r = await get_redis()
        await r.delete(f"lock:{key}")

    async def is_message_processed(self, message_id: str) -> bool:
        r = await get_redis()
        return bool(await r.exists(f"msg:{message_id}"))

    async def mark_message_processed(self, message_id: str, ttl: int = 86400) -> None:
        r = await get_redis()
        await r.setex(f"msg:{message_id}", ttl, "1")

    async def check_rate_limit(self, phone: str, limit: int) -> bool:
        r = await get_redis()
        key = f"rate:{phone}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 1)
        return count <= limit


cache_service = CacheService()
