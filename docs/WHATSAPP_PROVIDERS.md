# WhatsApp Provider Setup

ShopBot supports multiple WhatsApp API vendors. You do **not** need direct Meta Business API approval to get started.

## Configuration

```bash
WHATSAPP_PROVIDER=twilio          # primary
WHATSAPP_FALLBACK_PROVIDERS=wati,dialog360,meta
```

Outbound messages try the primary provider first, then fallbacks if send fails.

---

## Twilio (recommended for development)

**Why:** WhatsApp Sandbox works without Meta Business verification.

1. Sign up at [twilio.com](https://www.twilio.com/).
2. Console → Messaging → Try it out → Send a WhatsApp message → **Sandbox**.
3. Copy Account SID, Auth Token, and sandbox number (`whatsapp:+14155238886`).
4. Add to `.env`:

```bash
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ALLOWED_PHONES=+255700000000   # your phone after joining sandbox
```

5. Sandbox settings → **When a message comes in**: `https://YOUR_HOST/webhook`
6. On your phone, send the join code to the sandbox number (shown in Twilio console).
7. Message `help` to test the bot.

---

## WATI.io

**Why:** Popular for small shops; onboarding often simpler than direct Meta in TZ/EA region.

1. Create account at [wati.io](https://www.wati.io/).
2. Connect your WhatsApp number in WATI dashboard.
3. API & Webhooks → copy API token and base URL.

```bash
WHATSAPP_PROVIDER=wati
WATI_API_TOKEN=your_token
WATI_API_BASE_URL=https://live-server-xxxxx.wati.io
```

4. Set webhook URL: `https://YOUR_HOST/webhook/wati`

---

## 360dialog

**Why:** Certified Meta BSP; Cloud API compatible webhooks.

1. Register at [360dialog.com](https://www.360dialog.com/).
2. Complete their onboarding (they handle Meta relationship).
3. Copy API key from dashboard.

```bash
WHATSAPP_PROVIDER=dialog360
DIALOG360_API_KEY=your_api_key
DIALOG360_BASE_URL=https://waba-v2.360dialog.io
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

4. Webhook URL: `https://YOUR_HOST/webhook/dialog360`

---

## Meta Cloud API (when qualified)

```bash
WHATSAPP_PROVIDER=meta
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
```

Webhook: `GET/POST https://YOUR_HOST/webhook`

---

## Architecture

```
Inbound webhook → Provider.parse_webhook() → InboundMessage
                                              ↓
                                    message_handler
                                              ↓
Outbound reply  ← WhatsAppRouter.send_text() ← engines
                      (primary → fallback chain)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No reply | Check `ALLOWED_PHONES` includes your number (with `+`) |
| Twilio 401 | Verify SID and Auth Token |
| Twilio sandbox | Must join sandbox before messaging |
| Wrong provider parsing | Use dedicated URL `/webhook/twilio` or `/webhook/wati` |
| All providers fail | Logs show which provider failed; configure at least one |
