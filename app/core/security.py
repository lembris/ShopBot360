from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.constants import ROLE_PERMISSIONS, UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid token") from exc


def normalize_phone(phone: str) -> str:
    cleaned = phone.strip().replace(" ", "")
    if cleaned.startswith("0"):
        cleaned = "+255" + cleaned[1:]
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned


def is_phone_allowed(phone: str) -> bool:
    settings = get_settings()
    normalized = normalize_phone(phone)
    allowed = {normalize_phone(p) for p in settings.allowed_phone_list}
    return normalized in allowed


def require_permission(role: str, permission: str) -> None:
    perms = ROLE_PERMISSIONS.get(role, set())
    if permission not in perms:
        raise ForbiddenError(f"Role '{role}' cannot perform '{permission}'")
