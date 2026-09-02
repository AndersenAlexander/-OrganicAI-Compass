# Docker/PostgreSQL Runtime Recovery

Technical draft - local validation only.

Task 13B.0.3 uses a least-disruptive recovery order:

1. Inspect Docker Desktop, Docker API, WSL and Windows ports.
2. Validate PostgreSQL protocol, not only TCP acceptance.
3. Restart only the disposable test PostgreSQL container when the Docker API allows it.
4. Recreate only the disposable test container when the container is confirmed safe.
5. Restart Docker Desktop only when Docker API failures are global.
6. Stop and request manual action when Docker Desktop cannot start through the CLI.

Forbidden recovery actions:

- `docker compose down -v`
- Docker volume deletion
- Docker volume prune
- `docker system prune --volumes`
- Resetting `organicai_app`, `organicai_staging`, `organicai_staging_restore_validation`, `postgres`, `template0` or `template1`
- Reusing `organicai_staging_postgres_data`

Dedicated test service:

- Compose file: `docker-compose.postgres-test.yml`
- Container: `organicai-task13b03-postgres`
- Host binding: `127.0.0.1:55432`
- Database: `organicai_task13b03_test`
- Volume: `organicai_task13b03_postgres_data`
- Environment template: `.env.postgres-test.example`

Three-layer connectivity validation:

1. TCP: `Test-NetConnection 127.0.0.1 -Port 55432`
2. PostgreSQL readiness: `pg_isready -h 127.0.0.1 -p 55432`
3. Authenticated SQL: `SELECT version(); SELECT current_database(); SELECT current_user; SELECT 1;`

Task 13B.0.3 local result:

- Before restart, Docker API returned HTTP 500 while Docker Desktop reported `running`.
- TCP on `127.0.0.1:55432` was accepted by Docker backend, but psycopg2 timed out during PostgreSQL protocol handshake.
- A controlled `docker desktop restart` was attempted without deleting volumes.
- Docker Desktop then remained in `starting` and `docker version` reported `Docker Desktop is unable to start`.
- A follow-up `docker desktop start` and one explicit `stop`/`start` cycle also failed.
- WSL `docker-desktop` and `docker-desktop-data` ended in `Stopped`.
- The final PostgreSQL handshake changed to connection refused because Docker's port proxy was no longer listening.

Manual recovery is required in Docker Desktop UI or the host environment. Do not delete volumes during manual recovery.

Task 13B.0.3-R1 post-host-restart result:

- Windows was restarted manually before the R1 validation attempt.
- Docker context metadata remained readable and the active context stayed `desktop-linux`.
- `docker version`, `docker info`, `docker ps -a`, `docker volume ls`, `docker network ls` and `docker system df` failed with `Docker Desktop is unable to start`.
- Docker Desktop status remained `starting`.
- WSL `docker-desktop` and `docker-desktop-data` remained `Stopped`.
- Development services on `127.0.0.1:5190` and `127.0.0.1:8020` remained reachable.
- Staging and PostgreSQL test ports, including `55432`, were not listening.
- The dedicated PostgreSQL test service was not started and no migrations or PostgreSQL tests were run.
