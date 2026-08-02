from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import conversation, diagnostic, fear_transform, message, profile, recommendation, roadmap, roadmap_adaptation, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        from sqlalchemy import text
        with engine.begin() as connection:
            columns = {row[1] for row in connection.execute(text("PRAGMA table_info(users)"))}
            if "is_demo" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT 0"))
    if settings.app_env == "development":
        from app.models.profile import Profile
        from app.services.profile_generation import generate_profile_fallback

        with SessionLocal() as db:
            if db.get(Profile, "demo-profile") is None:
                data = generate_profile_fallback("demo-diagnostic", {
                    "interests": ["Education", "Human-AI Collaboration", "Sustainable Innovation"],
                    "values": ["Creativity", "Responsibility", "Contribution"],
                    "fears": "uncertainty about the future of work",
                    "preferred_orientation": "systems thinking",
                })
                db.add(Profile(id="demo-profile", diagnostic_id="demo-diagnostic", data=data))
                db.commit()
