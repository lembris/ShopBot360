import json
from typing import Any

from app.core.constants import SESSION_TTL_SECONDS
from app.services.redis import get_redis


class SessionService:
    def _key(self, shop_id: str, phone: str) -> str:
        return f"session:{shop_id}:{phone}"

    async def get(self, shop_id: str, phone: str) -> dict[str, Any] | None:
        r = await get_redis()
        raw = await r.get(self._key(shop_id, phone))
        if not raw:
            return None
        return json.loads(raw)

    async def set(self, shop_id: str, phone: str, data: dict[str, Any]) -> None:
        r = await get_redis()
        await r.setex(
            self._key(shop_id, phone),
            SESSION_TTL_SECONDS,
            json.dumps(data),
        )

    async def clear(self, shop_id: str, phone: str) -> None:
        r = await get_redis()
        await r.delete(self._key(shop_id, phone))

    async def update(self, shop_id: str, phone: str, **fields: Any) -> dict[str, Any]:
        data = await self.get(shop_id, phone) or {}
        data.update(fields)
        await self.set(shop_id, phone, data)
        return data


session_service = SessionService()
