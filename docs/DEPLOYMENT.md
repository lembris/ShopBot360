# Deploy ShopBot to a Server

This guide deploys the full stack (API, PostgreSQL, Redis, Celery, Nginx) on a **Linux VPS** using Docker. Minimum server: **2 GB RAM**, **2 vCPU**, Ubuntu 22.04/24.04.

## What you need before starting

| Item | Notes |
|------|--------|
| VPS | DigitalOcean, Hetzner, AWS Lightsail, Contabo, etc. |
| Domain (recommended) | For HTTPS webhook — Meta/Twilio require public URL |
| WhatsApp provider | Twilio Sandbox or WATI (see [WHATSAPP_PROVIDERS.md](WHATSAPP_PROVIDERS.md)) |
| SSH access | `ssh root@YOUR_SERVER_IP` |

---

## Step 1 — Prepare the server

```bash
# On your laptop — copy project to server (or use git)
ssh root@YOUR_SERVER_IP

apt update && apt upgrade -y
apt install -y git curl

# Create app user (optional but recommended)
adduser shopbot
usermod -aG sudo shopbot
su - shopbot
```

### Option A: Git clone

```bash
git clone https://github.com/YOUR_USER/WhatsBotShop.git
cd WhatsBotShop
```

### Option B: Upload from your PC

```powershell
# From Windows (PowerShell)
scp -r F:\Projects\WhatsBotShop shopbot@YOUR_SERVER_IP:~/
```

---

## Step 2 — Configure environment

```bash
cd ~/WhatsBotShop   # or your path
cp .env.production.example .env
nano .env
```

**Required values:**

```bash
POSTGRES_PASSWORD=<strong-password>
APP_SECRET_KEY=<random-32-chars>
JWT_SECRET=<random-32-chars>

WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

ALLOWED_PHONES=+255XXXXXXXXX
RUN_SEED=true
```

Generate secrets:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database first-run (automatic)

On **first deploy** (empty Postgres volume), Docker:

1. Creates `POSTGRES_USER` + `POSTGRES_DB` (from `.env`, default `shopbot`)
2. Runs `docker/postgres/init/01-init-shopbot.sh` — extensions, grants, timezone
3. API container runs **Alembic migrations** (all tables)
4. If `RUN_SEED=true`, creates demo shop + products + owner user

You do **not** need to manually `CREATE USER` or `CREATE DATABASE`.

To verify after deploy:

```bash
docker compose -f docker/docker-compose.prod.yml exec postgres \
  psql -U shopbot -d shopbot -c "SELECT * FROM _shopbot_init;"
```

---

## Step 3 — Deploy with Docker

```bash
chmod +x scripts/deploy.sh docker/entrypoint.sh
./scripts/deploy.sh
```

Or manually:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
```

Check status:

```bash
docker compose -f docker/docker-compose.prod.yml ps
curl http://localhost/health
# {"status":"ok","service":"whatsapp-shop-bot"}
```

---

## Step 4 — Open firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Step 5 — Point domain to server

1. In your domain DNS panel, add an **A record**:
   - Host: `@` or `bot` (e.g. `bot.yourshop.com`)
   - Value: `YOUR_SERVER_IP`
2. Wait 5–30 minutes for DNS propagation.

Test:

```bash
curl http://bot.yourshop.com/health
```

---

## Step 6 — Enable HTTPS (Let's Encrypt)

WhatsApp webhooks require **HTTPS** in production.

```bash
cd ~/WhatsBotShop
DOMAIN=bot.yourshop.com

# Get certificate (nginx must be running on port 80)
docker compose -f docker/docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email you@example.com \
  --agree-tos \
  --no-eff-email
```

Edit `docker/nginx.prod.conf`:

1. Replace `YOUR_DOMAIN` with `$DOMAIN` in the SSL server block.
2. Uncomment the entire `listen 443 ssl` server block.

Reload nginx:

```bash
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -s reload
```

Verify:

```bash
curl https://bot.yourshop.com/health
```

Enable auto-renewal:

```bash
docker compose -f docker/docker-compose.prod.yml --profile ssl up -d certbot
```

---

## Step 7 — Connect WhatsApp (Twilio)

1. Twilio Console → **Messaging** → **WhatsApp Sandbox**.
2. **When a message comes in**:  
   `https://bot.yourshop.com/webhook`
3. Method: **POST**
4. Join sandbox from your phone (send join code to sandbox number).
5. WhatsApp message: `help`

You should get the command menu back.

---

## Step 8 — Post-deploy checklist

- [ ] Set `RUN_SEED=false` in `.env` after first successful start
- [ ] Restart: `docker compose -f docker/docker-compose.prod.yml --env-file .env up -d`
- [ ] Change seed password via admin API if using dashboard
- [ ] Test: `sell 2 soda 1500`, `stock all`, `report today`
- [ ] Optional: enable Ollama AI:  
  `docker compose -f docker/docker-compose.prod.yml --profile ai up -d ollama`

---

## Useful commands

```bash
# Logs
docker compose -f docker/docker-compose.prod.yml logs -f api

# Restart API only
docker compose -f docker/docker-compose.prod.yml restart api

# Run migrations manually
docker compose -f docker/docker-compose.prod.yml exec api alembic upgrade head

# Backup database
./scripts/backup.sh

# Update app (after git pull)
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
```

---

## Admin dashboard (optional)

Build on server or locally and serve behind nginx:

```bash
cd dashboard
npm install && npm run build
# Copy dist/ behind nginx or use VITE_API_URL=https://bot.yourshop.com npm run build
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `502 Bad Gateway` | Wait for API healthcheck; `docker compose ... logs api` |
| Webhook not firing | URL must be HTTPS; Twilio debugger shows delivery errors |
| Unauthorized phone | Add number to `ALLOWED_PHONES` with country code `+255...` |
| DB connection error | Check `POSTGRES_PASSWORD` matches in `.env` and compose |
| Out of memory | Use 2GB+ VPS; disable `ollama` profile if not needed |

---

## Architecture on server

```
Internet → :443/:80 Nginx → API :8000
                              ├── PostgreSQL (internal)
                              ├── Redis (internal)
                              ├── Celery worker
                              └── Celery beat
```

Webhook path: `https://your-domain/webhook`
