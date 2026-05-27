"""Simple invoice text generation."""

from decimal import Decimal

from app.utils.currency import format_money


def generate_invoice(
    invoice_no: str,
    customer: str,
    lines: list[tuple[str, int, Decimal]],
    currency: str = "TZS",
) -> str:
    total = sum(qty * price for _, qty, price in lines)
    body = [f"INVOICE #{invoice_no}", f"Customer: {customer}", ""]
    for name, qty, price in lines:
        body.append(f"{qty} x {name} @ {format_money(price, currency)}")
    body.append(f"TOTAL: {format_money(total, currency)}")
    return "\n".join(body)
