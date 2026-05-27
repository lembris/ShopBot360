import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    shop_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        shop_id=shop_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_=metadata,
    )
    db.add(entry)
