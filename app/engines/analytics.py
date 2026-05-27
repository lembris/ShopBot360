import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.parser.validators import validate_role_for_intent
from app.schemas.parser import IntentResult
from app.utils.currency import format_money
from app.utils.dates import today_range


class AnalyticsEngine:
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

        if intent.intent == "profit_today":
            start, end = today_range(timezone)
            result = await db.execute(
                select(
                    func.coalesce(func.sum(SaleItem.total), 0),
                    func.coalesce(
                        func.sum(SaleItem.qty * func.coalesce(Product.cost_price, Product.price * 0)),
                        0,
                    ),
                )
                .join(Product, Product.id == SaleItem.product_id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .where(Sale.shop_id == shop_id, Sale.sold_at >= start, Sale.sold_at < end)
            )
            row = result.one()
            revenue = Decimal(str(row[0] or 0))
            cost = Decimal(str(row[1] or 0))
            profit = revenue - cost
            return (
                f"Profit today:\n"
                f"Revenue: {format_money(revenue, currency)}\n"
                f"Cost: {format_money(cost, currency)}\n"
                f"Profit: {format_money(profit, currency)}"
            )

        if intent.intent == "sales_customer":
            customer = intent.entities.customer
            if not customer:
                return "Usage: sales john"
            result = await db.execute(
                select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
                    Sale.shop_id == shop_id,
                    func.lower(Sale.customer_name) == customer.lower(),
                )
            )
            total = Decimal(str(result.scalar() or 0))
            return f"Sales for {customer.title()}: {format_money(total, currency)}"

        return "Analytics command not available"


analytics_engine = AnalyticsEngine()
