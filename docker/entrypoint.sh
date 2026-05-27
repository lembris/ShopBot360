#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python - <<'PY'
import os, sys, time
import asyncio

async def wait():
    try:
        import asyncpg
    except ImportError:
        return
    url = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")
    if not url or "postgresql://" not in url:
        return
    for i in range(60):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            print("PostgreSQL is ready.")
            return
        except Exception as e:
            if i == 59:
                print(f"PostgreSQL not ready: {e}", file=sys.stderr)
                sys.exit(1)
            time.sleep(2)

asyncio.run(wait())
PY

echo "Running database migrations..."
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "Seeding database..."
  python scripts/seed_data.py
fi

echo "Starting application..."
exec "$@"
