#!/usr/bin/env bash
# Obtain Let's Encrypt cert for mobinna.com (host certbot, same as outreach).
# Usage: sudo ./scripts/setup-ssl-mobinna.sh [email]
set -euo pipefail

DOMAIN="mobinna.com"
EMAIL="${1:-admin@mobinna.com}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NGINX_DIR="/var/www/outreach/nginx"
CERTBOT_WEBROOT="/var/www/certbot"

echo "==> Requesting certificate for $DOMAIN and www.$DOMAIN"
certbot certonly \
  --webroot \
  -w "$CERTBOT_WEBROOT" \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive

echo "==> Enabling HTTPS nginx config (outreach pattern)"
cp "$NGINX_DIR/mobinna.ssl.conf" "$NGINX_DIR/mobinna.conf"

docker exec outreach_nginx nginx -t
docker exec outreach_nginx nginx -s reload

echo ""
echo "==> SSL ready"
echo "Webhook URL: https://$DOMAIN/webhook"
echo "Health:      https://$DOMAIN/health"
echo ""
echo "Renewal: system certbot.timer + /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh"
