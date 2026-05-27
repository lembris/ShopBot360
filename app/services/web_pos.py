import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditType, PaymentMethod
from app.core.exceptions import InsufficientStockError, NotFoundError, ValidationError
from app.core.security import require_permission
from app.database.models.credit_ledger import CreditLedger
from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.database.transaction import transactional
from app.parser.validators import validate_stock
from app.services import audit
from app.utils.formatter import format_receipt
from app.utils.helpers import generate_receipt_no


async def checkout_cart(
    db: AsyncSession,
    *,
    shop_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
    items: list[dict],
    payment_method: str,
    customer_name: str | None,
    currency: str = "TZS",
) -> dict:
    require_permission(role, "sales")

    if not items:
        raise ValidationError("Cart is empty")

    try:
        method = PaymentMethod(payment_method)
    except ValueError as exc:
        raise ValidationError(f"Invalid payment method: {payment_method}") from exc

    is_credit = method == PaymentMethod.CREDIT
    customer = customer_name.strip() if customer_name else None
    if is_credit and not customer:
        raise ValidationError("Customer name required for credit sales")

    merged: dict[uuid.UUID, int] = {}
    for line in items:
        product_id = uuid.UUID(str(line["product_id"]))
        qty = int(line["qty"])
        if qty <= 0:
            raise ValidationError("Quantity must be positive")
        merged[product_id] = merged.get(product_id, 0) + qty

    products: dict[uuid.UUID, Product] = {}
    for product_id, qty in merged.items():
        product = await db.get(Product, product_id)
        if not product or product.shop_id != shop_id or not product.is_active:
            raise NotFoundError("Product not found")
        try:
            validate_stock(product, qty)
        except InsufficientStockError as exc:
            raise HTTPException(409, str(exc)) from exc
        products[product_id] = product

    receipt_no = generate_receipt_no(shop_id)
    line_rows: list[tuple[str, int, Decimal]] = []
    total = Decimal("0")

    async with transactional(db):
        sale = Sale(
            shop_id=shop_id,
            receipt_no=receipt_no,
            customer_name=customer,
            total_amount=Decimal("0"),
            payment_method=method.value,
            is_credit=is_credit,
            sold_by=user_id,
        )
        db.add(sale)
        await db.flush()

        for product_id, qty in merged.items():
            product = products[product_id]
            line_total = product.price * qty
            total += line_total
            product.stock_qty -= qty
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    qty=qty,
                    unit_price=product.price,
                    total=line_total,
                )
            )
            line_rows.append((product.name, qty, line_total))

        sale.total_amount = total

        if is_credit and customer:
            db.add(
                CreditLedger(
                    shop_id=shop_id,
                    customer_name=customer,
                    amount=total,
                    type=CreditType.DEBT,
                    created_by=user_id,
                    note=f"Sale {receipt_no}",
                )
            )

        await audit.log_action(
            db,
            shop_id=shop_id,
            user_id=user_id,
            action="sale_created",
            entity_type="sale",
            entity_id=receipt_no,
            metadata={"items": len(line_rows), "total": str(total), "source": "web_pos"},
        )

    payment_label = {
        PaymentMethod.CASH: "Cash",
        PaymentMethod.CREDIT: "Credit",
        PaymentMethod.MOBILE: "Mobile",
    }[method]

    receipt_text = format_receipt(
        receipt_no=receipt_no,
        lines=line_rows,
        total=total,
        payment_method=payment_label,
        currency=currency,
    )

    return {
        "id": str(sale.id),
        "receipt_no": receipt_no,
        "customer_name": customer,
        "total_amount": float(total),
        "payment_method": method.value,
        "is_credit": is_credit,
        "receipt_text": receipt_text,
        "items": [
            {
                "product_id": str(products[product_id].id),
                "product_name": products[product_id].name,
                "qty": qty,
                "unit_price": float(products[product_id].price),
                "total": float(products[product_id].price * qty),
            }
            for product_id, qty in merged.items()
        ],
    }
