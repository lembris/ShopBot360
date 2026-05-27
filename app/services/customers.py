import uuid

from sqlalchemy import func, select, union
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.credit_ledger import CreditLedger
from app.database.models.sale import Sale
from app.engines.debt import debt_engine
from app.services.sales import sale_items_summaries


async def list_customers(db: AsyncSession, shop_id: uuid.UUID) -> list[dict]:
    sales_names = select(Sale.customer_name.label("name")).where(
        Sale.shop_id == shop_id,
        Sale.customer_name.isnot(None),
        Sale.customer_name != "",
    )
    ledger_names = select(CreditLedger.customer_name.label("name")).where(
        CreditLedger.shop_id == shop_id
    )
    names_result = await db.execute(union(sales_names, ledger_names))
    names = sorted({row.name.strip() for row in names_result.all() if row.name and row.name.strip()})

    customers: list[dict] = []
    for name in names:
        sales_result = await db.execute(
            select(
                func.coalesce(func.sum(Sale.total_amount), 0),
                func.count(Sale.id),
                func.max(Sale.sold_at),
            ).where(
                Sale.shop_id == shop_id,
                func.lower(Sale.customer_name) == name.lower(),
            )
        )
        total_sales, sale_count, last_sale_at = sales_result.one()
        balance = await debt_engine.customer_balance(db, shop_id, name)
        customers.append(
            {
                "name": name,
                "balance": float(balance),
                "total_sales": float(total_sales or 0),
                "sale_count": int(sale_count or 0),
                "last_sale_at": last_sale_at.isoformat() if last_sale_at else None,
            }
        )

    customers.sort(key=lambda c: (-c["balance"], -c["total_sales"]))
    return customers


async def customer_ledger(
    db: AsyncSession,
    shop_id: uuid.UUID,
    customer_name: str,
    limit: int = 20,
) -> dict:
    balance = await debt_engine.customer_balance(db, shop_id, customer_name)

    ledger_result = await db.execute(
        select(CreditLedger)
        .where(
            CreditLedger.shop_id == shop_id,
            func.lower(CreditLedger.customer_name) == customer_name.lower(),
        )
        .order_by(CreditLedger.created_at.desc())
        .limit(limit)
    )
    entries = [
        {
            "id": str(entry.id),
            "type": entry.type,
            "amount": float(entry.amount),
            "note": entry.note,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
        for entry in ledger_result.scalars().all()
    ]

    sales_result = await db.execute(
        select(Sale)
        .where(
            Sale.shop_id == shop_id,
            func.lower(Sale.customer_name) == customer_name.lower(),
        )
        .order_by(Sale.sold_at.desc())
        .limit(limit)
    )
    sale_rows = sales_result.scalars().all()
    summaries = await sale_items_summaries(db, [sale.id for sale in sale_rows])
    sales = [
        {
            "id": str(sale.id),
            "receipt_no": sale.receipt_no,
            "product_names": summaries.get(sale.id, ""),
            "total_amount": float(sale.total_amount),
            "payment_method": sale.payment_method,
            "is_credit": sale.is_credit,
            "sold_at": sale.sold_at.isoformat() if sale.sold_at else None,
        }
        for sale in sale_rows
    ]

    return {
        "name": customer_name,
        "balance": float(balance),
        "ledger": entries,
        "sales": sales,
    }
