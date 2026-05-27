import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, InsufficientStockError, NotFoundError, ValidationError
from app.core.security import require_permission
from app.database.models.product import Product
from app.utils.helpers import slugify_name


async def find_product(
    db: AsyncSession,
    shop_id: uuid.UUID,
    name: str,
) -> Product:
    slug = slugify_name(name)
    result = await db.execute(
        select(Product).where(
            Product.shop_id == shop_id,
            Product.is_active.is_(True),
            func.lower(Product.name).contains(slug),
        )
    )
    product = result.scalars().first()
    if not product:
        raise NotFoundError(f"Product '{name}' not found")
    return product


def validate_role_for_intent(role: str, intent: str) -> None:
    sales_intents = {"sell"}
    inventory_intents = {"stock_add", "restock", "stock_all", "new_product", "price", "delete"}
    report_intents = {"report_today", "report_week", "top_products", "profit_today", "sales_customer"}
    debt_intents = {"debt", "payment", "credit_report"}
    analytics_intents = {"profit_today", "top_products", "sales_customer"}

    if intent in sales_intents:
        require_permission(role, "sales")
    elif intent in inventory_intents:
        require_permission(role, "inventory") if role != UserRole.OWNER else None
        if role == UserRole.CASHIER:
            raise ForbiddenError("Cashiers cannot manage inventory")
    elif intent in report_intents:
        require_permission(role, "reports")
    elif intent in debt_intents:
        require_permission(role, "debt") if role != UserRole.OWNER else None
        if role == UserRole.CASHIER:
            raise ForbiddenError("Cashiers cannot manage debt")
    elif intent in analytics_intents:
        require_permission(role, "analytics") if role != UserRole.OWNER else None


def validate_stock(product: Product, qty: int) -> None:
    if qty <= 0:
        raise ValidationError("Quantity must be positive")
    if product.stock_qty < qty:
        raise InsufficientStockError(
            f"Insufficient stock for {product.name}: have {product.stock_qty}, need {qty}"
        )


def validate_price(price: Decimal) -> None:
    if price <= 0:
        raise ValidationError("Price must be positive")
