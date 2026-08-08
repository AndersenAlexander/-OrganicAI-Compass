from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import advanced, assessments, auth, chat, conversations, demo, diagnostics, learning, profile_tools, profiles, rag, recommendations, research, roadmap, users, voice

settings = get_settings()
init_db()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(demo.auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
app.include_router(roadmap.router, prefix="/api/roadmap", tags=["roadmap"])
app.include_router(roadmap.api_router, prefix="/api", tags=["roadmap adaptation"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(research.router, prefix="/api/admin/research", tags=["research"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(profile_tools.router, prefix="/api", tags=["profile tools"])
app.include_router(advanced.router, prefix="/api", tags=["advanced"])
app.include_router(assessments.router, prefix="/api/v1", tags=["assessments"])
app.include_router(learning.router, prefix="/api/v1", tags=["learning"])
if settings.demo_account_enabled:
    app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
app.mount("/media", StaticFiles(directory="app/media"), name="media")

@app.on_event("startup")
async def seed_demo_on_startup() -> None:
    if settings.demo_account_enabled:
        from app.database import SessionLocal
        from app.services.demo_seed_service import ensure_demo
        with SessionLocal() as db:
            ensure_demo(db, reset=settings.demo_reset_on_startup)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
