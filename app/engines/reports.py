import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.parser.validators import validate_role_for_intent
from app.schemas.parser import IntentResult
from app.services.cache import cache_service
from app.utils.currency import format_money
from app.utils.dates import today_range, week_range


class ReportEngine:
    async def execute(
        self,
        db: AsyncSession,
        *,
        shop_id: uuid.UUID,
        role: str,
        intent: IntentResult,
        timezone: str = "Africa/Dar_es_Salaam",
        currency: str = "TZS",
    ) -> str:
        validate_role_for_intent(role, intent.intent)
        cache_key = f"report:{shop_id}:{intent.intent}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        if intent.intent == "report_today":
            start, end = today_range(timezone)
            msg = await self._sales_summary(db, shop_id, start, end, "Today", currency)
        elif intent.intent == "report_week":
            start, end = week_range(timezone)
            msg = await self._sales_summary(db, shop_id, start, end, "This week", currency)
        elif intent.intent == "top_products":
            msg = await self._top_products(db, shop_id, currency)
        else:
            return "Report not available"

        await cache_service.set(cache_key, msg)
        return msg

    async def _sales_summary(
        self,
        db: AsyncSession,
        shop_id: uuid.UUID,
        start,
        end,
        label: str,
        currency: str,
    ) -> str:
        result = await db.execute(
            select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
                Sale.shop_id == shop_id,
                Sale.sold_at >= start,
                Sale.sold_at < end,
            )
        )
        total = Decimal(str(result.scalar() or 0))
        return f"{label} sales: {format_money(total, currency)}"

    async def _top_products(self, db: AsyncSession, shop_id: uuid.UUID, currency: str) -> str:
        result = await db.execute(
            select(Product.name, func.sum(SaleItem.qty).label("qty"))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.shop_id == shop_id)
            .group_by(Product.name)
            .order_by(func.sum(SaleItem.qty).desc())
            .limit(5)
        )
        rows = result.all()
        if not rows:
            return "No sales data yet."
        lines = ["Top products:"]
        for name, qty in rows:
            lines.append(f"- {name}: {qty} sold")
        return "\n".join(lines)


report_engine = ReportEngine()
