#!/usr/bin/env bash
# Deploy ShopBot on a Linux VPS (Ubuntu 22.04+)
# Usage: ./scripts/deploy.sh [domain]
set -euo pipefail

DOMAIN="${1:-}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "==> ShopBot deploy in $REPO_DIR"

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  echo "Log out and back in if docker permission denied, then re-run."
fi

if ! docker compose version &>/dev/null; then
  echo "Docker Compose plugin required."
  exit 1
fi

if [ ! -f .env ]; then
  echo "Creating .env from .env.production.example..."
  cp .env.production.example .env
  echo "IMPORTANT: Edit .env with real secrets before continuing."
  echo "  nano .env"
  exit 1
fi

# Ensure production mode
grep -q '^APP_ENV=production' .env || echo 'APP_ENV=production' >> .env
grep -q '^APP_DEBUG=false' .env || echo 'APP_DEBUG=false' >> .env

echo "==> Building and starting services..."
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build

echo "==> Waiting for API health..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1/health &>/dev/null; then
    echo "API is healthy."
    break
  fi
  sleep 2
done

if [ -n "$DOMAIN" ]; then
  echo ""
  echo "Next: Point DNS A record for $DOMAIN to this server's IP."
  echo "Then run SSL setup:"
  echo "  docker compose -f docker/docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --agree-tos -m admin@$DOMAIN --no-eff-email"
  echo "See docs/DEPLOYMENT.md for full SSL steps."
fi

echo ""
echo "==> Deployment complete"
echo "Webhook URL (Twilio): https://YOUR_DOMAIN/webhook"
echo "Health check:         http://$(curl -s ifconfig.me 2>/dev/null || echo YOUR_SERVER_IP)/health"
echo ""
echo "After first seed, set RUN_SEED=false in .env and restart:"
echo "  docker compose -f docker/docker-compose.prod.yml --env-file .env up -d"
