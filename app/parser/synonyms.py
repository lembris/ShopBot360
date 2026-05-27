import re

# Swahili number words → digits (used before regex matching)
SWAHILI_NUMBERS: dict[str, str] = {
    "moja": "1",
    "mbili": "2",
    "tatu": "3",
    "nne": "4",
    "tano": "5",
    "sita": "6",
    "saba": "7",
    "nane": "8",
    "tisa": "9",
    "kumi": "10",
}

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


def normalize_swahili_numbers(text: str) -> str:
    """Convert trailing or embedded Swahili number words to digits."""
    result = text
    for word, digit in SWAHILI_NUMBERS.items():
        result = re.sub(rf"\b{word}\b", digit, result, flags=re.IGNORECASE)
    return result


def expand_synonym_line(text: str) -> str:
    """Replace leading synonym with canonical keyword for regex matching."""
    normalized = normalize_swahili_numbers(normalize_text(text))
    for canonical, words in INTENT_SYNONYMS.items():
        for word in sorted(words, key=len, reverse=True):
            if normalized.startswith(word + " ") or normalized == word:
                return canonical + normalized[len(word) :]
    return normalized
