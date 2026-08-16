from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def docker_stat(name: str) -> dict[str, str | None]:
    try:
        output = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}", name],
            text=True,
            timeout=10,
        ).strip()
        if "|" in output:
            cpu, memory = output.split("|", 1)
            return {"cpu": cpu.strip(), "memory": memory.strip()}
    except Exception:
        pass
    return {"cpu": None, "memory": None}


def postgres_connections() -> int | None:
    try:
        output = subprocess.check_output(
            [
                "docker",
                "compose",
                "--env-file",
                ".env.staging",
                "-f",
                "docker-compose.staging.yml",
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "organicai_staging",
                "-d",
                "organicai_staging",
                "-t",
                "-A",
                "-c",
                "select count(*) from pg_stat_activity where datname='organicai_staging';",
            ],
            text=True,
            timeout=10,
            cwd=Path(__file__).resolve().parents[3],
        ).strip()
        return int(output)
    except Exception:
        return None


def login(base_url: str) -> tuple[str | None, str | None]:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        response = client.post("/api/auth/demo-login")
        response.raise_for_status()
        body = response.json()
        return body.get("access_token"), body.get("active_profile_id")


def request_once(base_url: str, token: str | None, endpoint: str) -> tuple[bool, float, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    started = time.perf_counter()
    try:
        with httpx.Client(base_url=base_url, timeout=10.0, follow_redirects=False) as client:
            response = client.get(endpoint, headers=headers)
        elapsed = (time.perf_counter() - started) * 1000
        return response.status_code < 500, elapsed, response.status_code
    except Exception:
        elapsed = (time.perf_counter() - started) * 1000
        return False, elapsed, 0


def run_phase(base_url: str, duration: int, concurrency: int, endpoints: list[str], token: str | None) -> dict:
    deadline = time.perf_counter() + duration
    lock = threading.Lock()
    latencies: list[float] = []
    statuses: dict[str, int] = {}
    total = success = failed = 0

    def worker(index: int) -> None:
        nonlocal total, success, failed
        cursor = index
        while time.perf_counter() < deadline:
            endpoint = endpoints[cursor % len(endpoints)]
            cursor += 1
            ok, elapsed, status = request_once(base_url, token, endpoint)
            with lock:
                total += 1
                success += 1 if ok else 0
                failed += 0 if ok else 1
                latencies.append(elapsed)
                statuses[str(status)] = statuses.get(str(status), 0) + 1

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, index) for index in range(concurrency)]
        for future in as_completed(futures):
            future.result()
    elapsed = max(0.001, time.perf_counter() - started)
    return {
        "durationSeconds": duration,
        "concurrency": concurrency,
        "totalRequests": total,
        "successfulRequests": success,
        "failedRequests": failed,
        "requestsPerSecond": round(total / elapsed, 3),
        "p50Ms": round(statistics.median(latencies), 2) if latencies else 0,
        "p95Ms": round(percentile(latencies, 95), 2),
        "p99Ms": round(percentile(latencies, 99), 2),
        "errorRate": round(failed / total, 4) if total else 0,
        "statusCounts": statuses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local staging performance baseline with synthetic requests only.")
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--phase1-duration", type=int, default=60)
    parser.add_argument("--phase1-concurrency", type=int, default=5)
    parser.add_argument("--phase2-duration", type=int, default=60)
    parser.add_argument("--phase2-concurrency", type=int, default=10)
    parser.add_argument("--output", default="../evidence/task13a/performance-baseline.json")
    args = parser.parse_args()

    token, profile_id = login(args.base_url)
    endpoints = [
        "/",
        "/health",
        "/health/ready",
        "/api/auth/me",
        "/api/v1/assessments/human-potential-career-assessment",
        "/api/privacy/summary",
    ]
    if profile_id:
        endpoints.extend(
            [
                f"/api/profiles/{profile_id}",
                f"/api/v1/profiles/{profile_id}/assessment-results",
                f"/api/v1/profiles/{profile_id}/career-resilience",
            ]
        )

    phase1 = run_phase(args.base_url, args.phase1_duration, args.phase1_concurrency, endpoints, token)
    phase2 = run_phase(args.base_url, args.phase2_duration, args.phase2_concurrency, endpoints, token)
    resources = {
        "backend": docker_stat("organicai-staging-backend"),
        "postgres": docker_stat("organicai-staging-postgres"),
        "proxy": docker_stat("organicai-staging-proxy"),
        "worker": docker_stat("organicai-staging-worker"),
        "postgresConnections": postgres_connections(),
    }
    report = {
        "formatVersion": 1,
        "label": "Local staging performance baseline - not a production capacity test.",
        "baseUrl": args.base_url,
        "phases": [phase1, phase2],
        "resources": resources,
        "externalProviderCalls": False,
        "secretValuesIncluded": False,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
