import json
import logging
from abc import ABC, abstractmethod
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.parser.intents import Intent
from app.schemas.parser import IntentResult, ParsedEntity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You parse WhatsApp shop commands for East African small businesses.
Return ONLY valid JSON with keys: intent, confidence (0-1), qty, product, price, customer, amount.
Intents: sell, stock_add, restock, stock_all, new_product, price, delete, report_today, report_week,
top_products, profit_today, debt, payment, credit_report, help, unknown.
Languages: English and Swahili. Example: "john amelipa 3000" -> payment, customer john, amount 3000."""


class AIProvider(ABC):
    @abstractmethod
    async def parse(self, text: str) -> IntentResult:
        ...


class OllamaProvider(AIProvider):
    async def parse(self, text: str) -> IntentResult:
        settings = get_settings()
        payload = {
            "model": settings.ollama_model,
            "prompt": f"{SYSTEM_PROMPT}\n\nUser message: {text}",
            "stream": False,
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                parsed = json.loads(data.get("response", "{}"))
        except Exception as exc:
            logger.warning("Ollama parse failed: %s", exc)
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                needs_clarification=True,
                clarification_prompt="Could not understand. Please rephrase.",
            )

        intent = parsed.get("intent", Intent.UNKNOWN)
        confidence = float(parsed.get("confidence", 0.5))
        entities = ParsedEntity(
            qty=int(parsed["qty"]) if parsed.get("qty") else None,
            product=parsed.get("product"),
            price=Decimal(str(parsed["price"])) if parsed.get("price") else None,
            customer=parsed.get("customer"),
            amount=Decimal(str(parsed["amount"])) if parsed.get("amount") else None,
        )
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_text=text,
            needs_clarification=confidence < settings.ai_confidence_threshold,
            clarification_prompt="Can you clarify your request?" if confidence < settings.ai_confidence_threshold else None,
        )


class AIFallbackService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider or OllamaProvider()

    async def parse(self, text: str) -> IntentResult:
        return await self.provider.parse(text)


ai_fallback_service = AIFallbackService()
