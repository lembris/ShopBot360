# WhatsApp Shop Bot

Production-grade WhatsApp commerce assistant for small shops — POS, inventory, credit tracking, reports, and AI-assisted commands (Swahili + English).

## Stack

- **API:** FastAPI + SQLAlchemy async
- **Database:** PostgreSQL 16
- **Cache / sessions:** Redis 7
- **Workers:** Celery + Beat
- **AI fallback:** Ollama (local LLM)
- **Admin UI:** React (Vite) in `dashboard/`
- **Mobile:** Flutter in `mobile/`

## Quick start

### 1. Environment

```bash
cp .env.example .env
# Edit WHATSAPP_* and ALLOWED_PHONES
```

### 2. Docker (recommended)

```bash
cd docker
docker compose up -d postgres redis
docker compose up api
```

### 3. Migrations & seed

```bash
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py
```

### 4. Run API locally

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Meta webhook

- Point webhook to `https://<your-host>/webhook`
- Verify token must match `WHATSAPP_VERIFY_TOKEN`
- Use ngrok for local dev: `ngrok http 8000`

### 6. Ollama (optional, Phase 2 AI)

```bash
cd docker
docker compose --profile ai up ollama -d
docker exec -it <ollama-container> ollama pull llama3.2
```

### 7. Admin dashboard

```bash
cd dashboard
npm install
npm run dev
```

Login with seeded owner phone and password `changeme` (set via seed).

### 8. Flutter mobile

```bash
cd mobile
flutter pub get
flutter run
```

## WhatsApp commands

| Command | Example |
|---------|---------|
| Sell | `sell 2 soda 1500` |
| Stock | `stock add sugar 50` |
| Report | `report today` |
| Debt | `debt john` |
| Payment | `paid john 5000` |
| Profit | `profit today` |
| Help | `help` |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/webhook` | WhatsApp webhook |
| POST | `/admin/auth/login` | JWT login |
| GET | `/admin/products` | List products |
| GET | `/admin/sales` | List sales |
| GET | `/admin/reports` | Reports |
| POST | `/admin/shops/onboard` | Create shop (SaaS) |
| GET | `/metrics` | Prometheus metrics |

## Project structure

```
app/
  api/          # Webhook, admin, billing routes
  core/         # Config, security, middleware
  database/     # Models + migrations
  engines/      # POS, inventory, debt, reports, analytics
  parser/       # Command parser + Ollama fallback
  services/     # WhatsApp, Redis, sessions, OCR, voice
  workers/      # Celery tasks
dashboard/      # React admin UI
mobile/         # Flutter companion app
docker/         # Dockerfile, compose, nginx
scripts/        # seed_data.py, backup.sh
```

## Tests

```bash
pytest app/tests -v
```

## Production

- Use `docker/docker-compose.yml` with nginx + SSL (Let's Encrypt)
- Run `scripts/backup.sh` via cron for PostgreSQL backups
- Set `SENTRY_DSN` for error tracking

## Phases implemented

1. **Phase 1:** WhatsApp webhook, parser, POS, inventory, reports
2. **Phase 2:** Debt/credit, Ollama AI, Celery workers, analytics, React dashboard
3. **Phase 3:** Multi-tenant onboarding, Stripe billing hooks, Flutter mobile, nginx
4. **Phase 4:** Voice (Whisper), OCR receipts, forecasting, suppliers, loyalty/expenses modules
