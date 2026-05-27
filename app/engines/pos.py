import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditType, PaymentMethod
from app.database.models.credit_ledger import CreditLedger
from app.database.models.sale import Sale, SaleItem
from app.parser.validators import find_product, validate_price, validate_role_for_intent, validate_stock
from app.schemas.parser import IntentResult
from app.database.transaction import transactional
from app.services import audit
from app.services.cache import cache_service
from app.services.receipts import build_sale_receipt
from app.utils.helpers import generate_receipt_no


class POSEngine:
    async def execute(
        self,
        db: AsyncSession,
        *,
        shop_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        intent: IntentResult,
        currency: str = "TZS",
        is_credit: bool = False,
    ) -> str:
        validate_role_for_intent(role, intent.intent)
        e = intent.entities
        if not e.product or not e.qty or not e.price:
            return intent.clarification_prompt or "Please provide product, quantity and price."

        product = await find_product(db, shop_id, e.product)
        validate_stock(product, e.qty)
        validate_price(e.price)

        lock_key = f"sale:{product.id}"
        if not await cache_service.acquire_lock(lock_key):
            return "Sale in progress, please retry."

        try:
            total = e.price * e.qty
            receipt_no = generate_receipt_no(shop_id)

            async with transactional(db):
                product.stock_qty -= e.qty
                sale = Sale(
                    shop_id=shop_id,
                    receipt_no=receipt_no,
                    customer_name=e.customer,
                    total_amount=total,
                    payment_method=PaymentMethod.CREDIT if is_credit else PaymentMethod.CASH,
                    is_credit=is_credit,
                    sold_by=user_id,
                )
                db.add(sale)
                await db.flush()
                db.add(
                    SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        qty=e.qty,
                        unit_price=e.price,
                        total=total,
                    )
                )
                if is_credit and e.customer:
                    db.add(
                        CreditLedger(
                            shop_id=shop_id,
                            customer_name=e.customer,
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
                    metadata={"product": product.name, "qty": e.qty, "total": str(total)},
                )

            return build_sale_receipt(
                receipt_no=receipt_no,
                product_name=product.name,
                qty=e.qty,
                unit_price=e.price,
                total=total,
                payment_method="Credit" if is_credit else "Cash",
                currency=currency,
            )
        finally:
            await cache_service.release_lock(lock_key)


pos_engine = POSEngine()
