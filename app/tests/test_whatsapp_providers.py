from unittest.mock import AsyncMock, patch

import pytest

from app.services.whatsapp_providers.dialog360 import Dialog360Provider
from app.services.whatsapp_providers.meta import MetaCloudProvider
from app.services.whatsapp_providers.router import WhatsAppRouter
from app.services.whatsapp_providers.twilio import TwilioProvider
from app.services.whatsapp_providers.wati import WatiProvider


def test_meta_parse_text_message():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "255700000001",
                                    "id": "wamid.123",
                                    "type": "text",
                                    "text": {"body": "sell 2 soda 1500"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    msgs = MetaCloudProvider().parse_webhook(payload)
    assert len(msgs) == 1
    assert msgs[0].text == "sell 2 soda 1500"
    assert msgs[0].from_phone == "255700000001"


def test_twilio_parse_form_message():
    form = {
        "From": "whatsapp:+255700000001",
        "Body": "report today",
        "MessageSid": "SM123",
        "NumMedia": "0",
    }
    msgs = TwilioProvider().parse_webhook(form=form)
    assert len(msgs) == 1
    assert msgs[0].text == "report today"
    assert msgs[0].from_phone == "+255700000001"


def test_wati_parse_message():
    payload = {
        "eventType": "message",
        "waId": "255700000001",
        "text": "stock all",
        "id": "wati-1",
    }
    msgs = WatiProvider().parse_webhook(payload)
    assert len(msgs) == 1
    assert msgs[0].text == "stock all"


def test_dialog360_delegates_meta_format():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "255700000001",
                                    "type": "text",
                                    "text": {"body": "help"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    msgs = Dialog360Provider().parse_webhook(payload)
    assert len(msgs) == 1
    assert msgs[0].text == "help"


@pytest.mark.asyncio
async def test_router_fallback_on_primary_failure():
    primary = AsyncMock()
    primary.name = "primary"
    primary.send_text = AsyncMock(side_effect=Exception("down"))
    fallback = AsyncMock()
    fallback.name = "fallback"
    fallback.send_text = AsyncMock(return_value={"ok": True})

    router = WhatsAppRouter(providers=[primary, fallback])
    result = await router.send_text("+255700000001", "hello")
    assert result == {"ok": True}
    fallback.send_text.assert_called_once()
