import re
import uuid
from datetime import datetime, timezone


def generate_receipt_no(shop_id: uuid.UUID) -> str:
    suffix = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    short = str(shop_id).split("-")[0][:4].upper()
    return f"{short}-{suffix}"


def slugify_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())
