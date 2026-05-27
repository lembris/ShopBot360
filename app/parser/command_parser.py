import re
from decimal import Decimal

from app.parser.intents import Intent
from app.parser.synonyms import expand_synonym_line, normalize_text
from app.schemas.parser import IntentResult, ParsedEntity

# Named-group patterns (spec improvement)
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        Intent.SELL,
        re.compile(
            r"^sell\s+(?P<qty>\d+)\s+(?P<product>.+?)\s+(?P<price>\d+)(?:\s+(?P<customer>.+))?$",
            re.I,
        ),
    ),
    (
        Intent.SELL,
        re.compile(r"^sell\s+(?P<product>.+?)\s+(?P<qty>\d+)$", re.I),
    ),
    (
        Intent.SELL,
        re.compile(r"^sell\s+(?P<product>.+?)$", re.I),
    ),
    (
        Intent.STOCK_ADD,
        re.compile(r"^stock\s+add\s+(?P<product>.+?)\s+(?P<qty>\d+)$", re.I),
    ),
    (
        Intent.RESTOCK,
        re.compile(r"^restock\s+(?P<product>.+?)\s+(?P<qty>\d+)$", re.I),
    ),
    (
        Intent.STOCK_ALL,
        re.compile(r"^stock\s+all$", re.I),
    ),
    (
        Intent.NEW_PRODUCT,
        re.compile(
            r"^new\s+(?P<product>.+?)\s+(?P<price>\d+)\s+(?P<qty>\d+)$",
            re.I,
        ),
    ),
    (
        Intent.PRICE,
        re.compile(r"^price\s+(?P<product>.+?)\s+(?P<price>\d+)$", re.I),
    ),
    (
        Intent.DELETE,
        re.compile(r"^delete\s+(?P<product>.+?)$", re.I),
    ),
    (
        Intent.REPORT_TODAY,
        re.compile(r"^report\s+today$", re.I),
    ),
    (
        Intent.REPORT_WEEK,
        re.compile(r"^report\s+week$", re.I),
    ),
    (
        Intent.TOP_PRODUCTS,
        re.compile(r"^top\s+products?$", re.I),
    ),
    (
        Intent.PROFIT_TODAY,
        re.compile(r"^profit\s+today$", re.I),
    ),
    (
        Intent.SALES_CUSTOMER,
        re.compile(r"^sales\s+(?P<customer>.+)$", re.I),
    ),
    (
        Intent.DEBT,
        re.compile(r"^debt\s+(?P<customer>.+)$", re.I),
    ),
    (
        Intent.PAYMENT,
        re.compile(r"^paid\s+(?P<customer>.+?)\s+(?P<amount>\d+)$", re.I),
    ),
    (
        Intent.CREDIT_REPORT,
        re.compile(r"^credit\s+report$", re.I),
    ),
    (
        Intent.HELP,
        re.compile(r"^help$", re.I),
    ),
]


class CommandParser:
    def parse(self, text: str) -> IntentResult:
        raw = text.strip()
        if not raw:
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                raw_text=raw,
                needs_clarification=True,
                clarification_prompt="Send a command like: sell 2 soda 1500",
            )

        expanded = expand_synonym_line(raw)
        normalized = normalize_text(expanded)

        if normalized == "report":
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                raw_text=raw,
                needs_clarification=True,
                clarification_prompt="Try: report today, report week, or top products",
            )
        if normalized == "stock add":
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                raw_text=raw,
                needs_clarification=True,
                clarification_prompt="Try: stock add sugar 50",
            )

        for intent, pattern in PATTERNS:
            match = pattern.match(normalized)
            if match:
                entities = self._extract_entities(match.groupdict())
                confidence = 0.95 if intent != Intent.SELL or entities.qty else 0.6
                needs_clarification = intent == Intent.SELL and not entities.qty
                prompt = None
                if needs_clarification:
                    prompt = f"How many {entities.product or 'items'} sold?"
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    entities=entities,
                    raw_text=raw,
                    needs_clarification=needs_clarification,
                    clarification_prompt=prompt,
                )

        return IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            raw_text=raw,
            needs_clarification=True,
            clarification_prompt=(
                "I didn't understand. Try:\n"
                "• sell 2 soda 1500\n"
                "• stock add sugar 50\n"
                "• report today\n"
                "• help"
            ),
        )

    def _extract_entities(self, groups: dict[str, str | None]) -> ParsedEntity:
        entities = ParsedEntity()
        if groups.get("qty"):
            entities.qty = int(groups["qty"])
        if groups.get("product"):
            entities.product = groups["product"].strip()
        if groups.get("price"):
            entities.price = Decimal(groups["price"])
        if groups.get("customer"):
            entities.customer = groups["customer"].strip()
        if groups.get("amount"):
            entities.amount = Decimal(groups["amount"])
        return entities
