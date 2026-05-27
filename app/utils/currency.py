from decimal import Decimal


def format_money(amount: Decimal | float | int, currency: str = "TZS") -> str:
    value = Decimal(str(amount))
    if currency == "TZS":
        return f"TZS {value:,.0f}"
    return f"{currency} {value:,.2f}"
