from decimal import Decimal

from app.utils.currency import format_money


def format_receipt(
    receipt_no: str,
    lines: list[tuple[str, int, Decimal]],
    total: Decimal,
    payment_method: str,
    currency: str = "TZS",
) -> str:
    body_lines = [f"RECEIPT #{receipt_no}"]
    for name, qty, line_total in lines:
        body_lines.append(f"{qty} x {name} {format_money(line_total, currency)}")
    body_lines.append(f"TOTAL: {format_money(total, currency)}")
    body_lines.append(f"Paid {payment_method.title()}")
    body_lines.append("Thank you")
    return "\n".join(body_lines)
