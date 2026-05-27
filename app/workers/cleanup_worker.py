import asyncio

from app.services.redis import get_redis
from app.workers.celery_app import celery_app


async def _cleanup() -> None:
    r = await get_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match="session:*", count=100)
        for key in keys:
            ttl = await r.ttl(key)
            if ttl == -1:
                await r.expire(key, 900)
        if cursor == 0:
            break


@celery_app.task(name="app.workers.cleanup_worker.cleanup_stale_sessions")
def cleanup_stale_sessions() -> None:
    asyncio.run(_cleanup())
