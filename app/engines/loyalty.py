"""Customer loyalty points (extensibility module)."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.sale import Sale

POINTS_PER_1000 = 1


class LoyaltyEngine:
    async def points_for_customer(
        self, db: AsyncSession, shop_id: uuid.UUID, customer_name: str
    ) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
                Sale.shop_id == shop_id,
                func.lower(Sale.customer_name) == customer_name.lower(),
            )
        )
        total = Decimal(str(result.scalar() or 0))
        return int(total / 1000) * POINTS_PER_1000

    async def status(self, db: AsyncSession, shop_id: uuid.UUID, customer: str) -> str:
        pts = await self.points_for_customer(db, shop_id, customer)
        return f"{customer.title()} loyalty points: {pts}"


loyalty_engine = LoyaltyEngine()
