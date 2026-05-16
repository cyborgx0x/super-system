# Super System

Dashboard + Django control plane for workspace services.

## Current architecture

- Django app: templates + resource UI + resource APIs in `backend/`.
- OAuth endpoints: served by Django and reuse connector adapters in `backend/connectors/`.
- Reverse proxy: root nginx gateway forwards localhost traffic to super-system Django service.
- Container build: one Dockerfile (`super-system/Dockerfile`) with two targets:
	- `backend` for Django runtime
	- `gateway` for nginx gateway image

## Security model

- `client_id` / `client_secret` are kept in backend RAM only during OAuth session TTL.
- Access tokens are stored in browser local storage vault for the active user profile.
- No `.env.connectors` file is required for dashboard OAuth flow.

## Persistence

- SQLite database path defaults to `/app/data/db.sqlite3`.
- In docker-compose, map `./data/super-system:/app/data` to persist DB on host.
