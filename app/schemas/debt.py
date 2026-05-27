from decimal import Decimal

from pydantic import BaseModel


class DebtSummary(BaseModel):
    customer_name: str
    balance: Decimal
