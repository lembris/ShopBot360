"""Business expenses tracking (extensibility — stored in audit metadata for MVP)."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.transaction import transactional
from app.services import audit


class ExpensesEngine:
    async def record_expense(
        self,
        db: AsyncSession,
        *,
        shop_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str,
        amount: Decimal,
        note: str | None = None,
    ) -> str:
        async with transactional(db):
            await audit.log_action(
                db,
                shop_id=shop_id,
                user_id=user_id,
                action="expense_recorded",
                entity_type="expense",
                metadata={"category": category, "amount": str(amount), "note": note},
            )
        return f"Expense recorded: {category} {amount}"


expenses_engine = ExpensesEngine()
