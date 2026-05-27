# PostgreSQL first-run initialization

Scripts in this folder are mounted to `/docker-entrypoint-initdb.d/` and run **only once** when the `pgdata` Docker volume is empty (first deploy).

The official Postgres image already creates:

- User from `POSTGRES_USER` (default: `shopbot`)
- Database from `POSTGRES_DB` (default: `shopbot`)
- Password from `POSTGRES_PASSWORD`

`01-init-shopbot.sh` then:

1. Enables `pgcrypto` and `uuid-ossp`
2. Sets database timezone to `Africa/Dar_es_Salaam`
3. Grants schema privileges to the app user
4. Records init in `_shopbot_init` table

**Re-run init:** remove the volume and redeploy:

```bash
docker compose -f docker/docker-compose.prod.yml down
docker volume rm whatsbotshop_pgdata   # name may vary: docker volume ls
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d
```

Schema tables are created by **Alembic** on API startup (`docker/entrypoint.sh`), not by these scripts.
