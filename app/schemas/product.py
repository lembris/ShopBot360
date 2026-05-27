from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductRead(BaseModel):
    id: UUID
    name: str
    price: Decimal
    stock_qty: int
    reorder_at: int

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    price: Decimal
    stock_qty: int = 0
    cost_price: Decimal | None = None
