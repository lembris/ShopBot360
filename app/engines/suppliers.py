"""Supplier purchase order drafts when stock is low."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product


class SupplierEngine:
    async def draft_purchase_orders(self, db: AsyncSession, shop_id: uuid.UUID) -> str:
        result = await db.execute(
            select(Product).where(
                Product.shop_id == shop_id,
                Product.is_active.is_(True),
                Product.stock_qty <= Product.reorder_at,
            )
        )
        low = result.scalars().all()
        if not low:
            return "No purchase orders needed."
        lines = ["PO Draft:"]
        for p in low:
            order_qty = max(p.reorder_at * 2, 10)
            lines.append(f"- {p.name}: order {order_qty} {p.unit}")
        return "\n".join(lines)


supplier_engine = SupplierEngine()
