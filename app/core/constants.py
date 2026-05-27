from enum import StrEnum


class UserRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"
    VIEWER = "viewer"


class CreditType(StrEnum):
    DEBT = "debt"
    PAYMENT = "payment"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CREDIT = "credit"
    MOBILE = "mobile"


ROLE_PERMISSIONS: dict[str, set[str]] = {
    UserRole.OWNER: {"sales", "inventory", "reports", "analytics", "debt", "admin", "products"},
    UserRole.MANAGER: {"sales", "inventory", "reports", "analytics", "products"},
    UserRole.CASHIER: {"sales"},
    UserRole.VIEWER: {"reports"},
}

DEFAULT_TIMEZONE = "Africa/Dar_es_Salaam"
DEFAULT_CURRENCY = "TZS"
SESSION_TTL_SECONDS = 900
MESSAGE_DEDUP_TTL_SECONDS = 86400
REPORT_CACHE_TTL_SECONDS = 600
