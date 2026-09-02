# Container Architecture

Technical draft — requires legal and operational review before public deployment.

Backend and frontend images use multi-stage builds. Final images run as non-root users, exclude local environment files, local databases, backups, reports and development dependency directories. Alembic migrations run in the dedicated migrator container, not in backend workers.

Backend runtime command uses Uvicorn with one worker by default for local staging. Future orchestrators may scale by adding backend container replicas after readiness and session policy are validated.
