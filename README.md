## HookRelay
 HookRelay is a webhook delivery service. It accepts events via an authenticated API, stores them durably in PostgreSQL, and delivers them to configured endpoints with signed requests, bounded retries, and an auditable attempt history.

## Requirements - Python 3.14, Docker, Git

Local Setup:
-clone the repo
-create and activate virtualenv
-install with pip install -e ".[dev]"
run tests with pytest tests -v

Database (from D05):

-docker compose up -d
-docker compose ps — wait for (healthy)
-Connect: docker compose exec db psql -U hookrelay -d hookrelay
-Stop: docker compose stop db

## Current status

- D01–D06 complete: Python project, canonical JSON, hashing, HTTP routes, PostgreSQL container, CI
- 22 tests passing
- CI: GitHub Actions runs `pytest tests -v` on push and PR
- No delivery logic yet — this is a learning project in progress

## Not implemented yet

- No database schema or migrations
- No worker or delivery logic
- No retries, leases, or crash recovery
- No authentication
- No deployment