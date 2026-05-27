import re

# Map synonym tokens to canonical intent prefixes
INTENT_SYNONYMS: dict[str, list[str]] = {
    "sell": ["sell", "sold", "uza", "uza", "sale"],
    "stock": ["stock", "bidhaa", "stoki"],
    "restock": ["restock", "ongeza", "add"],
    "new": ["new", "add", "ongeza bidhaa"],
    "price": ["price", "bei"],
    "delete": ["delete", "futa", "ondoa"],
    "report": ["report", "mauzo", "ripoti"],
    "top": ["top", "best"],
    "debt": ["debt", "deni", "credit"],
    "paid": ["paid", "lipa", "amelipa", "payment"],
    "profit": ["profit", "faida"],
    "help": ["help", "msaada", "menu"],
}


def normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def expand_synonym_line(text: str) -> str:
    """Replace leading synonym with canonical keyword for regex matching."""
    normalized = normalize_text(text)
    for canonical, words in INTENT_SYNONYMS.items():
        for word in sorted(words, key=len, reverse=True):
            if normalized.startswith(word + " ") or normalized == word:
                return canonical + normalized[len(word) :]
    return normalized
