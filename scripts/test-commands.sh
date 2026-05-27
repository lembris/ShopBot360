#!/usr/bin/env bash
# Test all ShopBot commands via webhook simulation
set -euo pipefail

BASE="https://mobinna.com/webhook"
PHONE="+255746082561"
SID=0

post() {
  SID=$((SID + 1))
  local body="$1"
  local label="$2"
  echo ""
  echo "=== $label: '$body' ==="
  resp=$(curl -s -w "\nHTTP:%{http_code}" -X POST "$BASE" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "From=whatsapp:${PHONE}" \
    --data-urlencode "Body=${body}" \
    --data-urlencode "MessageSid=SMtest${SID}" \
    --data-urlencode "NumMedia=0")
  code=$(echo "$resp" | grep '^HTTP:' | cut -d: -f2)
  echo "HTTP: $code"
  echo "$resp" | grep -v '^HTTP:'
  sleep 1
}

post "help" "HELP"
post "report" "REPORT (bare)"
post "report today" "REPORT TODAY"
post "stock all" "STOCK ALL"
post "stock add" "STOCK ADD (incomplete)"
post "stock add sugar 50" "STOCK ADD sugar 50"
post "sell 2 soda 1500" "SELL complete"
post "report today" "REPORT TODAY after sale"
post "profit today" "PROFIT TODAY"
post "debt john" "DEBT john"
post "paid john 5000" "PAID john 5000"
post "credit report" "CREDIT REPORT"
post "top products" "TOP PRODUCTS"
post "report week" "REPORT WEEK"
post "uza soda mbili" "SWAHILI sell (partial)"
post "2" "SESSION qty follow-up"
post "1500" "SESSION price follow-up"
post "restock water 10" "RESTOCK"
post "price soda 1600" "PRICE UPDATE"
post "new juice 2000 20" "NEW PRODUCT"
