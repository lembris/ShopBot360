from enum import StrEnum


class Intent(StrEnum):
    SELL = "sell"
    STOCK_ADD = "stock_add"
    RESTOCK = "restock"
    STOCK_ALL = "stock_all"
    NEW_PRODUCT = "new_product"
    PRICE = "price"
    DELETE = "delete"
    REPORT_TODAY = "report_today"
    REPORT_WEEK = "report_week"
    TOP_PRODUCTS = "top_products"
    PROFIT_TODAY = "profit_today"
    SALES_CUSTOMER = "sales_customer"
    DEBT = "debt"
    PAYMENT = "payment"
    CREDIT_REPORT = "credit_report"
    HELP = "help"
    UNKNOWN = "unknown"
