from __future__ import annotations

import argparse

from alembic import command
from alembic.util.exc import CommandError

from app.config import get_settings
from app.db.migration_status import alembic_config, get_alembic_head


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Alembic management wrapper.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("current")
    subparsers.add_parser("history")
    subparsers.add_parser("heads")
    subparsers.add_parser("check")
    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--revision", default="head")
    upgrade_parser.add_argument("--allow-production", action="store_true")
    downgrade_parser = subparsers.add_parser("downgrade")
    downgrade_parser.add_argument("--revision", required=True)
    downgrade_parser.add_argument("--allow-production", action="store_true")
    stamp_parser = subparsers.add_parser("stamp")
    stamp_parser.add_argument("--revision", default="head")
    stamp_parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    config = alembic_config(settings)
    _, multiple = get_alembic_head(settings)
    if multiple:
        print("Multiple Alembic heads detected. Resolve heads before running migrations.")
        return 3
    try:
        if args.command in {"status", "current"}:
            command.current(config)
        elif args.command == "history":
            command.history(config)
        elif args.command == "heads":
            command.heads(config)
        elif args.command == "check":
            command.check(config)
        elif args.command == "upgrade":
            if settings.app_env == "production" and not args.allow_production:
                print("Production upgrade requires --allow-production.")
                return 1
            command.upgrade(config, args.revision)
        elif args.command == "downgrade":
            if settings.app_env == "production" or not args.allow_production:
                print("Downgrade is blocked unless explicitly allowed outside production.")
                return 1
            command.downgrade(config, args.revision)
        elif args.command == "stamp":
            if not args.apply:
                print("Stamp is dry-run by default. Re-run with --apply after schema validation.")
                return 1
            command.stamp(config, args.revision)
    except CommandError as exc:
        print(f"Alembic command failed: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
