import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product
from app.database.models.sale import SaleItem


def format_items_summary(lines: list[tuple[str, int]]) -> str:
    parts: list[str] = []
    for name, qty in lines:
        parts.append(f"{name} x{qty}" if qty > 1 else name)
    return ", ".join(parts)


async def sale_items_summaries(
    db: AsyncSession,
    sale_ids: list[uuid.UUID],
) -> dict[uuid.UUID, str]:
    if not sale_ids:
        return {}

    result = await db.execute(
        select(SaleItem.sale_id, Product.name, SaleItem.qty)
        .join(Product, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id.in_(sale_ids))
        .order_by(SaleItem.sale_id, Product.name)
    )

    grouped: dict[uuid.UUID, list[tuple[str, int]]] = {}
    for sale_id, name, qty in result.all():
        grouped.setdefault(sale_id, []).append((name, qty))

    return {sale_id: format_items_summary(lines) for sale_id, lines in grouped.items()}
