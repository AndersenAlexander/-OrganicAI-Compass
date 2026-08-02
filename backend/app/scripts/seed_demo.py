from app.config import get_settings
from app.database import SessionLocal, init_db
from app.services.demo_seed_service import ensure_demo
def main() -> None:
    settings=get_settings(); print(f"Demo mode: {settings.demo_mode}")
    if not settings.demo_mode: print("Set DEMO_MODE=true to seed the demo account."); return
    init_db()
    with SessionLocal() as db:
        user,profile,roadmap=ensure_demo(db)
        print(f"Demo email: {user.email}"); print(f"Profile ID: {profile.id}"); print(f"Roadmap ID: {roadmap.id}"); print("Completed demo seeding status: ready")
if __name__=="__main__": main()
