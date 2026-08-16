# Deployment Ordering

1. Provision database and secrets.
2. Build or select immutable images.
3. Run migration job.
4. Start backend.
5. Start worker.
6. Start frontend and proxy or ingress.
7. Run smoke tests.
8. Verify observability and backup.
