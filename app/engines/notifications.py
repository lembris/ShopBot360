from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.debt import debt_engine
from app.engines.reports import report_engine
from app.parser.intents import Intent
from app.schemas.parser import IntentResult
from app.utils.currency import format_money


def format_low_stock_alert(products: list[tuple[str, int]]) -> str:
    lines = ["Low stock:"]
    for name, qty in products:
        lines.append(f"- {name}: {qty} left")
    return "\n".join(lines)


def format_daily_summary(sales: Decimal, profit: Decimal, credits: Decimal, currency: str) -> str:
    return (
        f"Daily Summary\n"
        f"Sales: {format_money(sales, currency)}\n"
        f"Profit: {format_money(profit, currency)}\n"
        f"Credits: {format_money(credits, currency)}"
    )


async def format_debt_reminder(
    db: AsyncSession, shop_id, customer: str, currency: str
) -> str:
    balance = await debt_engine.customer_balance(db, shop_id, customer)
    return f"Reminder: {customer.title()} owes {format_money(balance, currency)}"


async def build_daily_report_message(
    db: AsyncSession,
    shop_id,
    timezone: str,
    currency: str,
) -> str:
    sales_msg = await report_engine.execute(
        db,
        shop_id=shop_id,
        role="owner",
        intent=IntentResult(intent=Intent.REPORT_TODAY),
        timezone=timezone,
        currency=currency,
    )
    return f"Daily Summary\n{sales_msg}"
