"""Stock forecasting based on recent sales velocity."""

import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.utils.dates import get_shop_tz


class ForecastingEngine:
    async def reorder_suggestions(
        self,
        db: AsyncSession,
        shop_id: uuid.UUID,
        days: int = 7,
        limit: int = 5,
    ) -> str:
        tz = get_shop_tz("Africa/Dar_es_Salaam")
        since = __import__("datetime").datetime.now(tz) - timedelta(days=days)

        result = await db.execute(
            select(
                Product.id,
                Product.name,
                Product.stock_qty,
                Product.reorder_at,
                func.coalesce(func.sum(SaleItem.qty), 0).label("sold"),
            )
            .outerjoin(SaleItem, SaleItem.product_id == Product.id)
            .outerjoin(Sale, Sale.id == SaleItem.sale_id)
            .where(
                Product.shop_id == shop_id,
                Product.is_active.is_(True),
            )
            .group_by(Product.id)
            .having(func.coalesce(func.sum(SaleItem.qty), 0) > 0)
        )
        suggestions = []
        for row in result.all():
            daily_rate = row.sold / max(days, 1)
            days_left = row.stock_qty / daily_rate if daily_rate > 0 else 999
            if row.stock_qty <= row.reorder_at or days_left < 3:
                suggestions.append((row.name, row.stock_qty, int(daily_rate * 7)))
        suggestions.sort(key=lambda x: x[1])
        if not suggestions:
            return "No reorder suggestions this week."
        lines = ["Reorder suggestions (7-day est.):"]
        for name, stock, order_qty in suggestions[:limit]:
            lines.append(f"- {name}: {stock} left, order ~{order_qty}")
        return "\n".join(lines)


forecasting_engine = ForecastingEngine()
