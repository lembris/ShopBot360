from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ParsedEntity:
    qty: int | None = None
    product: str | None = None
    price: Decimal | None = None
    customer: str | None = None
    amount: Decimal | None = None
    stock_delta: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentResult:
    intent: str
    confidence: float = 1.0
    entities: ParsedEntity = field(default_factory=ParsedEntity)
    raw_text: str = ""
    needs_clarification: bool = False
    clarification_prompt: str | None = None
