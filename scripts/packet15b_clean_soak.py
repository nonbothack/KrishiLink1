"""Clean steady-state Packet 15B soak (no deliberate outages).

The script records HTTP latency plus bounded runtime resource snapshots. It is
run against the isolated Docker Compose project only.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone

import httpx


def docker_cmd(*args: str) -> str:
    docker = os.environ.get("DOCKER_BIN", "docker")
    env = os.environ.copy()
    env.setdefault("DOCKER_HOST", "npipe:////./pipe/dockerDesktopLinuxEngine")
    env.setdefault("DOCKER_CONFIG", os.path.join(os.environ.get("TEMP", ""), "krishilink-docker-config-15a"))
    result = subprocess.run([docker, *args], capture_output=True, text=True, timeout=20, env=env)
    return result.stdout.strip()


def snapshot() -> dict:
    stats = docker_cmd("stats", "--no-stream", "--format", "{{.Name}}|{{.MemUsage}}|{{.CPUPerc}}")
    selected = {}
    for line in stats.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3 and any(name in parts[0] for name in ("backend-1", "worker-1", "scheduler-1")):
            selected[parts[0]] = {"memory": parts[1], "cpu": parts[2]}
    pg = docker_cmd("exec", "krishilink_packet15-postgres-1", "psql", "-U", "krishilink", "-d", "krishilink", "-Atc", "select count(*) from pg_stat_activity")
    backlog = docker_cmd("exec", "krishilink_packet15-postgres-1", "psql", "-U", "krishilink", "-d", "krishilink", "-Atc", "select count(*) from outbox_events where status='PENDING'")
    redis_info = docker_cmd("exec", "krishilink_packet15-redis-1", "redis-cli", "INFO", "memory")
    redis_memory = next((line.split(":", 1)[1] for line in redis_info.splitlines() if line.startswith("used_memory:")), None)
    redis_keys = docker_cmd("exec", "krishilink_packet15-redis-1", "redis-cli", "DBSIZE")
    celery_keys = docker_cmd("exec", "krishilink_packet15-redis-1", "redis-cli", "--scan", "--pattern", "celery*").splitlines()
    return {"containers": selected, "postgres_connections": pg, "outbox_pending": backlog, "redis_used_memory_bytes": redis_memory, "redis_key_count": redis_keys, "celery_keys": len(celery_keys)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=1800)
    parser.add_argument("--rps", type=float, default=5)
    parser.add_argument("--url", default="http://127.0.0.1:8001/api/v1/health/ready")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    start = datetime.now(timezone.utc).isoformat()
    resource_start = snapshot()
    stop_at = time.monotonic() + args.duration
    interval = 1.0 / args.rps
    lock = threading.Lock()
    latencies: list[float] = []
    codes: dict[str, int] = {}
    errors = 0

    def request_once(client: httpx.Client) -> None:
        nonlocal errors
        began = time.perf_counter()
        try:
            code = str(client.get(args.url).status_code)
        except Exception:
            code = "error"
        elapsed = (time.perf_counter() - began) * 1000
        with lock:
            latencies.append(elapsed)
            codes[code] = codes.get(code, 0) + 1
            if code == "error" or code.startswith("5"):
                errors += 1

    with httpx.Client(timeout=10.0) as client:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            next_at = time.monotonic()
            while time.monotonic() < stop_at:
                futures.append(executor.submit(request_once, client))
                next_at += interval
                time.sleep(max(0, next_at - time.monotonic()))
            concurrent.futures.wait(futures)
    latencies.sort()
    def percentile(q: float):
        return latencies[min(len(latencies) - 1, max(0, int(len(latencies) * q) - 1))] if latencies else None
    resource_end = snapshot()
    result = {"run_type": "CLEAN_STEADY_STATE_RUN", "started_at": start, "finished_at": datetime.now(timezone.utc).isoformat(), "duration_seconds": args.duration, "target_rps": args.rps, "requests": len(latencies), "codes": codes, "errors": errors, "p50_ms": percentile(.50), "p95_ms": percentile(.95), "p99_ms": percentile(.99), "max_ms": max(latencies) if latencies else None, "resource_start": resource_start, "resource_end": resource_end, "criteria": {"no_planned_outage": True, "error_rate_max": 0, "http_5xx_max": 0}}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
