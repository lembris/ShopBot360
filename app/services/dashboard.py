import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditType
from app.database.models.credit_ledger import CreditLedger
from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.database.models.shop import Shop
from app.utils.dates import get_shop_tz, today_range, week_range
from app.services.sales import sale_items_summaries


def _money(value: Decimal | float | int | None) -> float:
    return float(value or 0)


async def _sales_metrics(
    db: AsyncSession,
    shop_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> dict:
    result = await db.execute(
        select(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.count(Sale.id),
        ).where(
            Sale.shop_id == shop_id,
            Sale.sold_at >= start,
            Sale.sold_at < end,
        )
    )
    revenue, count = result.one()
    revenue = Decimal(str(revenue or 0))
    count = int(count or 0)
    avg = revenue / count if count else Decimal("0")
    return {
        "revenue": _money(revenue),
        "sales_count": count,
        "avg_order_value": _money(avg),
    }


async def _profit_metrics(
    db: AsyncSession,
    shop_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> dict:
    result = await db.execute(
        select(
            func.coalesce(func.sum(SaleItem.total), 0),
            func.coalesce(
                func.sum(SaleItem.qty * func.coalesce(Product.cost_price, 0)),
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
    margin = (profit / revenue * 100) if revenue else Decimal("0")
    return {
        "revenue": _money(revenue),
        "cost": _money(cost),
        "profit": _money(profit),
        "margin_pct": round(float(margin), 1),
    }


async def _inventory_metrics(db: AsyncSession, shop_id: uuid.UUID) -> dict:
    products_result = await db.execute(
        select(Product).where(Product.shop_id == shop_id, Product.is_active.is_(True))
    )
    products = products_result.scalars().all()
    total_units = sum(p.stock_qty for p in products)
    stock_value = sum(p.stock_qty * p.price for p in products)
    low_stock = [
        {
            "id": str(p.id),
            "name": p.name,
            "stock_qty": p.stock_qty,
            "reorder_at": p.reorder_at,
            "unit": p.unit,
        }
        for p in products
        if p.stock_qty <= p.reorder_at
    ]
    low_stock.sort(key=lambda item: item["stock_qty"])
    return {
        "product_count": len(products),
        "total_stock_units": total_units,
        "stock_value": _money(stock_value),
        "low_stock_count": len(low_stock),
        "low_stock": low_stock[:8],
    }


async def _debt_metrics(db: AsyncSession, shop_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(
            CreditLedger.customer_name,
            func.coalesce(
                func.sum(
                    case(
                        (CreditLedger.type == CreditType.DEBT, CreditLedger.amount),
                        else_=-CreditLedger.amount,
                    )
                ),
                0,
            ).label("balance"),
        )
        .where(CreditLedger.shop_id == shop_id)
        .group_by(CreditLedger.customer_name)
    )
    debtors = []
    total = Decimal("0")
    for name, balance in result.all():
        bal = Decimal(str(balance or 0))
        if bal > 0:
            debtors.append({"name": name, "balance": _money(bal)})
            total += bal
    debtors.sort(key=lambda item: item["balance"], reverse=True)
    return {
        "total_outstanding": _money(total),
        "debtor_count": len(debtors),
        "top_debtors": debtors[:5],
    }


async def _daily_sales_trend(
    db: AsyncSession,
    shop_id: uuid.UUID,
    timezone: str,
    days: int = 7,
) -> list[dict]:
    tz = get_shop_tz(timezone)
    now = datetime.now(tz)
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            func.date(Sale.sold_at),
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.count(Sale.id),
        )
        .where(Sale.shop_id == shop_id, Sale.sold_at >= start)
        .group_by(func.date(Sale.sold_at))
        .order_by(func.date(Sale.sold_at))
    )
    by_date = {
        str(row[0]): {"revenue": _money(row[1]), "sales_count": int(row[2] or 0)}
        for row in result.all()
    }

    trend = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date()
        key = str(day)
        point = by_date.get(key, {"revenue": 0.0, "sales_count": 0})
        trend.append(
            {
                "date": key,
                "label": day.strftime("%a %d"),
                "revenue": point["revenue"],
                "sales_count": point["sales_count"],
            }
        )
    return trend


async def _top_products(
    db: AsyncSession,
    shop_id: uuid.UUID,
    limit: int = 5,
) -> list[dict]:
    result = await db.execute(
        select(
            Product.name,
            func.coalesce(func.sum(SaleItem.qty), 0),
            func.coalesce(func.sum(SaleItem.total), 0),
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(Sale.shop_id == shop_id)
        .group_by(Product.name)
        .order_by(func.sum(SaleItem.total).desc())
        .limit(limit)
    )
    return [
        {
            "name": name,
            "qty_sold": int(qty or 0),
            "revenue": _money(revenue),
        }
        for name, qty, revenue in result.all()
    ]


async def _recent_sales(db: AsyncSession, shop_id: uuid.UUID, limit: int = 8) -> list[dict]:
    result = await db.execute(
        select(Sale)
        .where(Sale.shop_id == shop_id)
        .order_by(Sale.sold_at.desc())
        .limit(limit)
    )
    sales = result.scalars().all()
    summaries = await sale_items_summaries(db, [sale.id for sale in sales])
    return [
        {
            "id": str(sale.id),
            "receipt_no": sale.receipt_no,
            "customer_name": sale.customer_name,
            "product_names": summaries.get(sale.id, ""),
            "total_amount": _money(sale.total_amount),
            "payment_method": sale.payment_method,
            "is_credit": sale.is_credit,
            "sold_at": sale.sold_at.isoformat() if sale.sold_at else None,
        }
        for sale in sales
    ]


async def build_dashboard(db: AsyncSession, shop: Shop) -> dict:
    shop_id = shop.id
    timezone = shop.timezone or "Africa/Dar_es_Salaam"
    currency = shop.currency or "TZS"
    today_start, today_end = today_range(timezone)
    week_start, week_end = week_range(timezone)

    today_sales = await _sales_metrics(db, shop_id, today_start, today_end)
    week_sales = await _sales_metrics(db, shop_id, week_start, week_end)
    today_profit = await _profit_metrics(db, shop_id, today_start, today_end)
    week_profit = await _profit_metrics(db, shop_id, week_start, week_end)

    all_time_result = await db.execute(
        select(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.count(Sale.id),
        ).where(Sale.shop_id == shop_id)
    )
    all_revenue, all_count = all_time_result.one()

    return {
        "shop_name": shop.name,
        "currency": currency,
        "timezone": timezone,
        "generated_at": datetime.now(get_shop_tz(timezone)).isoformat(),
        "today": {
            **today_sales,
            **today_profit,
        },
        "week": {
            **week_sales,
            **week_profit,
        },
        "all_time": {
            "revenue": _money(all_revenue),
            "sales_count": int(all_count or 0),
        },
        "inventory": await _inventory_metrics(db, shop_id),
        "debt": await _debt_metrics(db, shop_id),
        "daily_sales": await _daily_sales_trend(db, shop_id, timezone),
        "top_products": await _top_products(db, shop_id),
        "recent_sales": await _recent_sales(db, shop_id),
    }
