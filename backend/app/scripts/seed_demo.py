from app.config import get_settings
from app.database import SessionLocal
from app.services.demo_seed_service import ensure_demo


def main() -> None:
    settings = get_settings()
    print(f"Demo account enabled: {settings.demo_account_enabled}")
    if settings.app_env == "production":
        print("Demo seeding is disabled in production.")
        return
    if not settings.demo_account_enabled:
        print("Set DEMO_ACCOUNT_ENABLED=true to seed the demo account.")
        return
    with SessionLocal() as db:
        user, profile, roadmap = ensure_demo(db)
        print(f"Demo email: {user.email}")
        print(f"Profile ID: {profile.id}")
        print(f"Roadmap ID: {roadmap.id}")
        print("Completed demo seeding status: ready")


if __name__ == "__main__":
    main()
