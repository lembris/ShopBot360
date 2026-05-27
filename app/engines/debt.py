import uuid
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditType
from app.database.models.credit_ledger import CreditLedger
from app.parser.validators import validate_role_for_intent
from app.schemas.parser import IntentResult
from app.database.transaction import transactional
from app.services import audit
from app.utils.currency import format_money


class DebtEngine:
    async def customer_balance(
        self, db: AsyncSession, shop_id: uuid.UUID, customer_name: str
    ) -> Decimal:
        result = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (CreditLedger.type == CreditType.DEBT, CreditLedger.amount),
                            else_=-CreditLedger.amount,
                        )
                    ),
                    0,
                )
            ).where(
                CreditLedger.shop_id == shop_id,
                func.lower(CreditLedger.customer_name) == customer_name.lower(),
            )
        )
        return Decimal(str(result.scalar() or 0))

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

        if intent.intent == "debt":
            if not e.customer:
                return "Usage: debt john"
            balance = await self.customer_balance(db, shop_id, e.customer)
            return f"{e.customer.title()} owes {format_money(balance, currency)}"

        if intent.intent == "payment":
            if not e.customer or not e.amount:
                return "Usage: paid john 5000"
            async with transactional(db):
                db.add(
                    CreditLedger(
                        shop_id=shop_id,
                        customer_name=e.customer,
                        amount=e.amount,
                        type=CreditType.PAYMENT,
                        created_by=user_id,
                    )
                )
                await audit.log_action(
                    db,
                    shop_id=shop_id,
                    user_id=user_id,
                    action="payment_recorded",
                    entity_type="credit",
                    metadata={"customer": e.customer, "amount": str(e.amount)},
                )
            balance = await self.customer_balance(db, shop_id, e.customer)
            return (
                f"Recorded payment {format_money(e.amount, currency)} from {e.customer.title()}.\n"
                f"Remaining balance: {format_money(balance, currency)}"
            )

        if intent.intent == "credit_report":
            result = await db.execute(
                select(CreditLedger.customer_name).where(CreditLedger.shop_id == shop_id).distinct()
            )
            customers = [r[0] for r in result.all()]
            if not customers:
                return "No credit records."
            lines = ["Credit report:"]
            for name in customers:
                bal = await self.customer_balance(db, shop_id, name)
                if bal > 0:
                    lines.append(f"- {name.title()}: {format_money(bal, currency)}")
            return "\n".join(lines) if len(lines) > 1 else "All customers settled."

        return "Debt command not handled"


debt_engine = DebtEngine()
