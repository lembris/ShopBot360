import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.product import Product
from app.parser.validators import find_product, validate_price, validate_role_for_intent
from app.schemas.parser import IntentResult
from app.database.transaction import transactional
from app.services import audit
from app.utils.currency import format_money


class InventoryEngine:
    async def execute(
        self,
        db: AsyncSession,
        *,
        shop_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        intent: IntentResult,
        currency: str = "TZS",
    ) -> str:
        validate_role_for_intent(role, intent.intent)
        e = intent.entities
        intent_name = intent.intent

        if intent_name == "stock_all":
            return await self._list_stock(db, shop_id, currency)

        if intent_name == "new_product":
            if not e.product or e.price is None or e.qty is None:
                return "Usage: new sugar 3500 100"
            async with transactional(db):
                product = Product(
                    shop_id=shop_id,
                    name=e.product.title(),
                    price=e.price,
                    stock_qty=e.qty,
                )
                db.add(product)
                await db.flush()
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="product_created",
                    entity_type="product",
                    entity_id=str(product.id),
                )
            return f"Added {product.name} at {format_money(e.price, currency)}, stock {e.qty}"

        product = await find_product(db, shop_id, e.product or "")

        if intent_name == "stock_add":
            delta = e.qty or e.stock_delta or 0
            async with transactional(db):
                product.stock_qty += delta
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="stock_added",
                    entity_type="product",
                    entity_id=str(product.id),
                    metadata={"delta": delta},
                )
            return f"Stock updated: {product.name} now {product.stock_qty} {product.unit}"

        if intent_name == "restock":
            delta = e.qty or 0
            async with transactional(db):
                product.stock_qty += delta
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="restocked",
                    entity_type="product",
                    entity_id=str(product.id),
                    metadata={"delta": delta},
                )
            return f"Restocked {product.name}: +{delta}, total {product.stock_qty}"

        if intent_name == "price":
            if e.price is None:
                return "Usage: price sugar 4000"
            old = product.price
            async with transactional(db):
                product.price = e.price
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="price_changed",
                    entity_type="product",
                    entity_id=str(product.id),
                    metadata={"old": str(old), "new": str(e.price)},
                )
            return f"Price updated: {product.name} {format_money(e.price, currency)}"

        if intent_name == "delete":
            async with transactional(db):
                product.is_active = False
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="product_deleted",
                    entity_type="product",
                    entity_id=str(product.id),
                )
            return f"Removed product: {product.name}"

        return "Inventory command not handled"

    async def _list_stock(self, db: AsyncSession, shop_id: uuid.UUID, currency: str) -> str:
        result = await db.execute(
            select(Product).where(Product.shop_id == shop_id, Product.is_active.is_(True))
        )
        products = result.scalars().all()
        if not products:
            return "No products in stock."
        lines = ["Stock:"]
        for p in products:
            flag = " (!)" if p.stock_qty <= p.reorder_at else ""
            lines.append(
                f"- {p.name}: {p.stock_qty} {p.unit} @ {format_money(p.price, currency)}{flag}"
            )
        return "\n".join(lines)


inventory_engine = InventoryEngine()
