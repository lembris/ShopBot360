"""Subscription and trial scheduling helpers."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.subscription import Subscription


async def expire_trials(db: AsyncSession) -> list[str]:
    """Return shop IDs whose trials expired."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    result = await db.execute(
        select(Subscription).where(
            Subscription.plan == "trial",
            Subscription.status == "trialing",
            Subscription.created_at < cutoff,
        )
    )
    expired = []
    for sub in result.scalars().all():
        sub.status = "expired"
        expired.append(str(sub.shop_id))
    return expired
