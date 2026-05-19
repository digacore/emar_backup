# file_api

Bun HTTP service for desktop agent APIs (`/last_time`, `/get_credentials`, etc.). Nginx proxies these paths from `app.emarvault.com` to this container.

## Local development

```bash
bun install
export DATABASE_URL=postgresql://postgres:pass@127.0.0.1:5432/db
bun run index.ts
curl http://localhost:3000/health
```

## Production

See [docs/production-ops.md](docs/production-ops.md). On the server:

```bash
cd web && bash scripts/file-api-recover.sh
```

Requires Bun **1.2.3+** (uses `Bun.serve` routes API).
