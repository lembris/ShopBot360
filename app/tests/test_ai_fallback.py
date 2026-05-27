import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.parser.ai_fallback import AIFallbackService, OllamaProvider
from app.parser.intents import Intent
from app.schemas.parser import IntentResult


@pytest.mark.asyncio
async def test_ollama_parse_payment():
    mock_response = {
        "response": '{"intent": "payment", "confidence": 0.9, "customer": "john", "amount": 3000}'
    }
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.post = AsyncMock(return_value=mock_resp)
        provider = OllamaProvider()
        result = await provider.parse("john amelipa 3000")
        assert result.intent == "payment"
        assert float(result.confidence) >= 0.7


@pytest.mark.asyncio
async def test_ai_fallback_service():
    mock_provider = AsyncMock()
    mock_provider.parse = AsyncMock(
        return_value=IntentResult(intent=Intent.PAYMENT, confidence=0.95)
    )
    service = AIFallbackService(provider=mock_provider)
    result = await service.parse("test")
    assert result.intent == Intent.PAYMENT
