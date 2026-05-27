from decimal import Decimal

from app.utils.formatter import format_receipt


def build_sale_receipt(
    receipt_no: str,
    product_name: str,
    qty: int,
    unit_price: Decimal,
    total: Decimal,
    payment_method: str,
    currency: str = "TZS",
) -> str:
    return format_receipt(
        receipt_no=receipt_no,
        lines=[(product_name, qty, total)],
        total=total,
        payment_method=payment_method,
        currency=currency,
    )
