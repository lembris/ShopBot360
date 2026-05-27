from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SaleRead(BaseModel):
    id: UUID
    receipt_no: str
    customer_name: str | None
    total_amount: Decimal
    sold_at: datetime | None

    model_config = {"from_attributes": True}
