from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from app.services.database_admin import resolve_backend_path, utc_iso, utc_timestamp, write_json_atomic
from app.services.task11_4_finalization import write_legacy_artifact_access_report


BASE_URL = "http://127.0.0.1:8020"
STATE_PATH = resolve_backend_path("./tmp/task11-4-runtime-state.json")
SMOKE_REPORT = resolve_backend_path("../reports/database-integrity/final-postgres-runtime-smoke.json")
RESTART_REPORT = resolve_backend_path("../reports/database-integrity/final-postgres-restart-persistence.json")
ROLLBACK_REPORT = resolve_backend_path("../reports/database-integrity/rollback-rehearsal-task11-4.json")


class SmokeClient:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> tuple[int, Any]:
        data = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(self.base_url + path, data=data, method=method, headers=request_headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, _parse_json(body)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            return error.code, _parse_json(body)


def _parse_json(body: str) -> Any:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"textResponse": True}


def _check(checks: list[dict[str, Any]], name: str, passed: bool, *, status_code: int | None = None, detail: str = "") -> None:
    checks.append({"name": name, "passed": bool(passed), "statusCode": status_code, "detail": detail})


def _diagnostic_payload() -> dict[str, Any]:
    return {
        "interests": ["human AI collaboration", "learning systems"],
        "natural_activities": ["mapping ideas", "building prototypes"],
        "problems_noticed": ["unclear persistence handoffs"],
        "preferred_orientation": ["creative", "practical"],
        "fears": ["losing context"],
        "fear_intensity": 4,
        "ai_threat_or_opportunity": "AI should support human judgment with traceable context.",
        "unclear_future": "I want reliable persistence and rollback.",
        "desired_world": "Tools preserve evidence and keep people in control.",
        "values": ["agency", "privacy"],
        "contribution_if_supported": "Build careful AI collaboration workflows.",
        "skills": ["systems thinking", "communication"],
        "preferred_learning_style": ["project-based"],
        "cognitive_style": ["visual"],
        "ai_experience": "intermediate",
        "ai_tools_used": ["assistant"],
        "ai_confidence": 7,
        "ai_help_goals": ["organize work"],
        "preferred_interaction": "both",
        "raw_answers": {"task": "task11.4-runtime-smoke"},
    }


def _sha256_prefix(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def run_write_smoke(base_url: str = BASE_URL) -> dict[str, Any]:
    client = SmokeClient(base_url)
    checks: list[dict[str, Any]] = []
    suffix = utc_timestamp()
    email = f"task11-4-smoke-{suffix}@example.test"
    password = f"Task11Smoke-{suffix}"

    for path, name in [
        ("/health", "health"),
        ("/health/live", "liveness"),
        ("/health/ready", "readiness"),
        ("/api/system/persistence", "settings persistence diagnostics"),
    ]:
        status, body = client.request("GET", path)
        _check(checks, name, status == 200, status_code=status)
        if path == "/api/system/persistence":
            _check(checks, "active PostgreSQL status", body.get("driver") == "postgresql", status_code=status)
            _check(checks, "migration current", body.get("migrationState") == "current", status_code=status)

    status, body = client.request("POST", "/api/auth/register", payload={"name": "Task 11 Smoke", "email": email, "password": password})
    token = body.get("access_token") if isinstance(body, dict) else None
    user_id = body.get("user", {}).get("id") if isinstance(body, dict) else None
    _check(checks, "synthetic user registration", status == 200 and bool(token), status_code=status)

    status, body = client.request("POST", "/api/auth/login", payload={"email": email, "password": password})
    token = body.get("access_token") if isinstance(body, dict) else token
    _check(checks, "existing valid user login", status == 200 and bool(token), status_code=status)

    status, body = client.request("POST", "/api/auth/demo-login")
    _check(checks, "demo login", status == 200 and bool(body.get("access_token") if isinstance(body, dict) else None), status_code=status)

    status, body = client.request("GET", "/api/auth/me", token=token)
    _check(checks, "current user", status == 200 and body.get("email") == email, status_code=status)

    status, body = client.request("POST", "/api/diagnostics", payload=_diagnostic_payload(), token=token)
    profile_id = body.get("profile_id") if isinstance(body, dict) else None
    _check(checks, "diagnostic data", status == 200 and bool(profile_id), status_code=status)

    status, body = client.request("GET", "/api/profiles", token=token)
    _check(checks, "profile list", status == 200 and isinstance(body, list) and len(body) >= 1, status_code=status)

    status, body = client.request("GET", f"/api/profiles/{profile_id}", token=token)
    _check(checks, "profile details", status == 200 and body.get("id") == profile_id, status_code=status)

    status, body = client.request("GET", "/api/conversations", token=token)
    _check(checks, "valid conversation history", status == 200 and isinstance(body, list), status_code=status)

    status, body = client.request("POST", "/api/conversations", payload={"profile_id": profile_id, "title": "Task 11.4 smoke"}, token=token)
    conversation_id = body.get("id") if isinstance(body, dict) else None
    _check(checks, "creation of a new conversation", status == 200 and bool(conversation_id), status_code=status)

    status, body = client.request(
        "POST",
        "/api/chat",
        payload={
            "message": "Persist this Task 11.4 synthetic smoke message.",
            "profile_id": profile_id,
            "conversation_id": conversation_id,
            "mode": "text",
            "language": "en",
        },
        token=token,
        timeout=60,
    )
    _check(checks, "creation of a new message", status == 200 and bool(body.get("message_id") if isinstance(body, dict) else None), status_code=status)

    status, body = client.request("GET", f"/api/conversations/{conversation_id}", token=token)
    message_count = len(body.get("messages", [])) if isinstance(body, dict) else 0
    _check(checks, "reload and persistence of that message", status == 200 and message_count >= 2, status_code=status)

    status, body = client.request(
        "POST",
        "/api/recommendations/generate",
        payload={"profile_id": profile_id, "categories": [], "force_regenerate": True},
        token=token,
        timeout=60,
    )
    recommendations = body.get("recommendations", []) if isinstance(body, dict) else []
    recommendation_id = recommendations[0].get("id") if recommendations else None
    _check(checks, "recommendations", status == 200 and bool(recommendations), status_code=status)

    if recommendation_id:
        status, _body = client.request(
            "POST",
            f"/api/recommendations/{recommendation_id}/feedback",
            payload={"rating": 5, "relevant": True, "feedback_text": "Task 11.4 synthetic feedback.", "reason_code": "other"},
            token=token,
        )
        _check(checks, "recommendation feedback", status == 200, status_code=status)
    else:
        _check(checks, "recommendation feedback", False, detail="No recommendation was generated for feedback.")

    status, body = client.request("POST", "/api/roadmap/generate", payload={"profile_id": profile_id}, token=token, timeout=60)
    roadmap_id = body.get("id") if isinstance(body, dict) else None
    _check(checks, "roadmap", status == 200 and bool(roadmap_id), status_code=status)

    status, body = client.request(
        "POST",
        f"/api/roadmaps/{roadmap_id}/actions",
        payload={"title": "Task 11.4 smoke action", "description": "Synthetic persistence action.", "horizon": "thirty_days"},
        token=token,
    )
    action_id = body.get("id") if isinstance(body, dict) else None
    _check(checks, "roadmap action creation", status == 200 and bool(action_id), status_code=status)

    status, body = client.request("PATCH", f"/api/roadmap-actions/{action_id}", payload={"status": "in_progress"}, token=token)
    _check(checks, "roadmap action update", status == 200 and body.get("status") == "in_progress", status_code=status)

    query = urllib.parse.quote("human AI collaboration")
    status, body = client.request("GET", f"/api/rag/search?query={query}", token=token, timeout=60)
    _check(checks, "RAG metadata retrieval", status == 200 and "results" in body, status_code=status)

    status, body = client.request("POST", "/api/rag/ask", payload={"query": "How should humans verify AI outputs?", "profile_id": profile_id}, token=token, timeout=60)
    _check(checks, "RAG ask persistence", status == 200 and bool(body.get("rag_run_id") if isinstance(body, dict) else None), status_code=status)

    status, body = client.request("GET", "/api/voice/status", token=token)
    _check(checks, "live voice provider status", status == 200 and "liveVoiceEnabled" in body, status_code=status)

    status, body = client.request(
        "POST",
        "/api/elevenlabs/v1/chat/completions",
        payload={
            "model": "organicai-coach",
            "stream": True,
            "messages": [{"role": "user", "content": "Give one short safe persistence check."}],
            "elevenlabs_extra_body": {
                "organicai_user_id": user_id,
                "profile_id": profile_id,
                "app_conversation_id": conversation_id,
                "elevenlabs_conversation_id": "task11-voice-smoke",
                "route": "/coach",
                "language": "en",
            },
        },
        headers={"Authorization": "Bearer task11-local-smoke"},
        timeout=60,
    )
    _check(checks, "live voice custom LLM local stream", status == 200, status_code=status)

    status, body = client.request("GET", "/api/voice/conversations/task11-voice-smoke/latest-turn", token=token)
    _check(checks, "live voice latest-turn metadata storage", status == 200 and bool(body.get("messageId") if isinstance(body, dict) else None), status_code=status)

    status, body = client.request("GET", "/api/v1/research/studies", token=token)
    _check(checks, "research data", status == 200 and isinstance(body, list), status_code=status)

    _check(checks, "logout", True, detail="Client-side token discard only; no server logout endpoint exists.")

    state = {
        "email": email,
        "password": password,
        "conversationId": conversation_id,
        "profileId": profile_id,
        "createdAt": utc_iso(),
    }
    write_json_atomic(STATE_PATH, state)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "baseUrl": base_url,
        "authenticated": bool(token),
        "syntheticWriteChecks": len(checks),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False, "secretsIncluded": False},
    }
    write_json_atomic(SMOKE_REPORT, report)
    return report


def run_rollback_rehearsal(base_url: str = BASE_URL) -> dict[str, Any]:
    client = SmokeClient(base_url)
    checks: list[dict[str, Any]] = []
    fallback = resolve_backend_path("./data/organicai-clean.db")
    manifest_path = resolve_backend_path("./data/organicai-clean.manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    expected_hash = str(manifest.get("cleanDatabaseHash") or "")
    before_prefix = _sha256_prefix(fallback)

    for path, name in [
        ("/api/health", "legacy-compatible health"),
        ("/health", "health"),
        ("/health/live", "liveness"),
        ("/health/ready", "readiness"),
        ("/api/system/configuration", "runtime configuration"),
        ("/api/system/persistence", "settings persistence diagnostics"),
        ("/api/voice/status", "voice provider status"),
    ]:
        status, body = client.request("GET", path)
        _check(checks, name, status == 200, status_code=status)
        if path == "/health/ready" and isinstance(body, dict):
            database = body.get("database", {})
            _check(checks, "rollback ready uses SQLite", database.get("dialect") == "sqlite", status_code=status)
            _check(checks, "rollback migration current", database.get("migrationState") == "current", status_code=status)
        if path == "/api/system/persistence" and isinstance(body, dict):
            release_gate = body.get("releaseGate", {})
            _check(checks, "rollback persistence uses SQLite", body.get("driver") == "sqlite", status_code=status)
            _check(checks, "rollback schema version current", body.get("schemaVersion") == "0001_initial_schema", status_code=status)
            _check(checks, "rollback fallback available", bool(release_gate.get("rollbackFallbackAvailable")), status_code=status)
            _check(checks, "legacy original still evidence only", release_gate.get("originalDatabaseRole") == "immutable evidence", status_code=status)
            _check(checks, "legacy data loss remains zero", release_gate.get("legacyDataLoss") == 0, status_code=status)

    after_prefix = _sha256_prefix(fallback)
    _check(checks, "fallback file present", before_prefix is not None and after_prefix is not None)
    _check(checks, "fallback hash unchanged during rehearsal", before_prefix == after_prefix)
    _check(checks, "fallback hash matches manifest", bool(expected_hash) and before_prefix == expected_hash[:12])

    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "baseUrl": base_url,
        "mode": "rollback-readonly",
        "targetDriver": "sqlite",
        "databaseRole": "rollback fallback rehearsal",
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "cleanFallback": {
            "relativePath": "backend/data/organicai-clean.db",
            "matchesManifest": bool(expected_hash) and before_prefix == expected_hash[:12],
            "unchangedDuringRehearsal": before_prefix == after_prefix,
            "hashPrefixBefore": before_prefix,
            "hashPrefixAfter": after_prefix,
        },
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False, "secretsIncluded": False},
    }
    write_json_atomic(ROLLBACK_REPORT, report)
    return report


def run_artifact_access_probe(base_url: str = BASE_URL) -> dict[str, Any]:
    client = SmokeClient(base_url)
    targets = [
        ("legacy sqlite root", "/organicai.db"),
        ("clean fallback sqlite", "/data/organicai-clean.db"),
        ("database backup dump", "/backups/database/organicai-app-pre-activation-sample.dump"),
        ("legacy orphan archive", "/backups/legacy-orphans/organicai-orphan-messages-sample.db"),
        ("integrity report", "/reports/database-integrity/original-sqlite-before-task11-4.json"),
        ("media traversal legacy sqlite", "/media/../organicai.db"),
        ("api traversal legacy sqlite", "/api/system/persistence/../../organicai.db"),
    ]
    checks: list[dict[str, Any]] = []
    for artifact, path in targets:
        status, _body = client.request("GET", path)
        checks.append(
            {
                "artifact": artifact,
                "method": "GET",
                "statusCode": status,
                "accessible": 200 <= status < 300,
                "blocked": status in {400, 401, 403, 404, 405},
            }
        )
    report = write_legacy_artifact_access_report(checks)
    report["passed"] = not report["legacyArtifactsPubliclyAccessible"] and all(check["blocked"] for check in checks)
    write_json_atomic(resolve_backend_path("../reports/database-integrity/legacy-artifact-accessibility-proof.json"), report)
    return report


def run_restart_verification(base_url: str = BASE_URL) -> dict[str, Any]:
    client = SmokeClient(base_url)
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    status, body = client.request("GET", "/health/ready")
    _check(checks, "readiness after restart", status == 200, status_code=status)
    status, body = client.request("GET", "/api/system/persistence")
    _check(checks, "persistence status after restart", status == 200 and body.get("driver") == "postgresql", status_code=status)
    status, body = client.request("POST", "/api/auth/login", payload={"email": state["email"], "password": state["password"]})
    token = body.get("access_token") if isinstance(body, dict) else None
    _check(checks, "synthetic login after restart", status == 200 and bool(token), status_code=status)
    status, body = client.request("GET", f"/api/conversations/{state['conversationId']}", token=token)
    message_count = len(body.get("messages", [])) if isinstance(body, dict) else 0
    _check(checks, "persisted synthetic conversation after restart", status == 200 and message_count >= 2, status_code=status)
    status, body = client.request("GET", f"/api/profiles/{state['profileId']}", token=token)
    _check(checks, "persisted synthetic profile after restart", status == 200, status_code=status)
    report = {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "baseUrl": base_url,
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "privacy": {"messageContentIncluded": False, "rawIdentifiersIncluded": False, "secretsIncluded": False},
    }
    write_json_atomic(RESTART_REPORT, report)
    return report


def wait_until_ready(base_url: str = BASE_URL, timeout_seconds: int = 30) -> bool:
    client = SmokeClient(base_url)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            status, _body = client.request("GET", "/health/ready", timeout=5)
            if status == 200:
                return True
        except OSError:
            pass
        time.sleep(1)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 11.4 runtime smoke checks.")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--verify-restart", action="store_true")
    parser.add_argument("--rollback-readonly", action="store_true")
    parser.add_argument("--artifact-access-probe", action="store_true")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    if args.wait and not wait_until_ready(args.base_url):
        print(json.dumps({"status": "failed", "message": "Backend did not become ready."}, indent=2))
        return 1
    if args.rollback_readonly:
        report = run_rollback_rehearsal(args.base_url)
    elif args.artifact_access_probe:
        report = run_artifact_access_probe(args.base_url)
    elif args.verify_restart:
        report = run_restart_verification(args.base_url)
    else:
        report = run_write_smoke(args.base_url)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
