#!/usr/bin/env python3
"""Analyze anonymized Packet 16 sessions without inventing pilot evidence."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROLES = {"farmer", "buyer", "fpo"}
OUTCOMES = {"SUCCESS", "PARTIAL", "FAIL", "NOT_ATTEMPTED"}
ASSISTANCE = {"NONE", "PROMPT", "COACHED", "ABORTED"}
PARTICIPANT_PREFIX = "P16-"


def _validate(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError("sessions must be a JSON array")
    sessions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for session in records:
        if not isinstance(session, dict):
            raise ValueError("each session must be an object")
        for field in ("session_id", "participant_code", "role", "build", "tasks"):
            if field not in session:
                raise ValueError(f"missing session field: {field}")
        sid = session["session_id"]
        participant = session["participant_code"]
        if not isinstance(sid, str) or not sid.startswith("S16-"):
            raise ValueError("session_id must use the S16- prefix")
        if sid in seen:
            raise ValueError(f"duplicate session_id: {sid}")
        seen.add(sid)
        if not isinstance(participant, str) or not participant.startswith(PARTICIPANT_PREFIX):
            raise ValueError("participant_code must use the P16- prefix")
        if session["role"] not in ROLES:
            raise ValueError(f"unsupported role: {session['role']}")
        if not isinstance(session["tasks"], list):
            raise ValueError("tasks must be an array")
        for task in session["tasks"]:
            if not isinstance(task, dict):
                raise ValueError("each task must be an object")
            required = ("task_id", "outcome", "elapsed_ms", "assistance")
            if any(field not in task for field in required):
                raise ValueError("task is missing a required field")
            if task["outcome"] not in OUTCOMES:
                raise ValueError(f"unsupported outcome: {task['outcome']}")
            if task["assistance"] not in ASSISTANCE:
                raise ValueError(f"unsupported assistance: {task['assistance']}")
            if not isinstance(task["elapsed_ms"], int) or task["elapsed_ms"] < 0:
                raise ValueError("elapsed_ms must be a non-negative integer")
        sessions.append(session)
    return sessions


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"count": numerator, "n": denominator, "rate": round(numerator / denominator, 4) if denominator else None}


def analyze_records(records: Any) -> dict[str, Any]:
    sessions = _validate(records)
    if not sessions:
        return {"status": "NO_PILOT_DATA", "n": 0, "reason": "No anonymized participant sessions were supplied."}

    role_counts = Counter(session["role"] for session in sessions)
    tasks_by_role: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    all_tasks = []
    for session in sessions:
        for task in session["tasks"]:
            row = {**task, "role": session["role"], "session_id": session["session_id"]}
            all_tasks.append(row)
            task_id = task["task_id"]
            bucket = tasks_by_role[session["role"]].setdefault(
                task_id, {"attempted": 0, "success": 0, "outcomes": Counter(), "assistance": Counter(), "elapsed_ms": []}
            )
            bucket["outcomes"][task["outcome"]] += 1
            bucket["assistance"][task["assistance"]] += 1
            if task["outcome"] != "NOT_ATTEMPTED":
                bucket["attempted"] += 1
                bucket["elapsed_ms"].append(task["elapsed_ms"])
                if task["outcome"] == "SUCCESS" and task["assistance"] == "NONE":
                    bucket["success"] += 1

    task_summary: dict[str, Any] = {}
    for role, role_tasks in tasks_by_role.items():
        task_summary[role] = {}
        for task_id, bucket in role_tasks.items():
            attempted = bucket["attempted"]
            timings = bucket["elapsed_ms"]
            task_summary[role][task_id] = {
                "success_without_assistance": _rate(bucket["success"], attempted),
                "outcomes": dict(bucket["outcomes"]),
                "assistance": dict(bucket["assistance"]),
                "timing_ms": {
                    "n": len(timings),
                    "median": statistics.median(timings) if timings else None,
                    "min": min(timings) if timings else None,
                    "max": max(timings) if timings else None,
                },
            }

    comprehension_tasks = [task for task in all_tasks if "comprehension" in task]
    comprehension = Counter(task["comprehension"] for task in comprehension_tasks)
    issue_tasks = [task for task in all_tasks if task.get("issue_code") and task["issue_code"] != "NONE"]
    return {
        "status": "ANALYZED",
        "n": len(sessions),
        "participants_by_role": dict(role_counts),
        "task_attempts_n": sum(task["outcome"] != "NOT_ATTEMPTED" for task in all_tasks),
        "tasks": task_summary,
        "comprehension": {"counts": dict(comprehension), "n": len(comprehension_tasks)},
        "issues": {"counts": dict(Counter(task["issue_code"] for task in issue_tasks)), "n": len(issue_tasks)},
        "limitations": [
            "Convenience-panel evidence must not be generalized to the population.",
            "The analysis reports descriptive outcomes only; it does not infer adoption, causal uplift or satisfaction.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON export containing {schema_version, sessions}")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args(argv)
    source = Path(args.input)
    if not source.exists():
        print("NO PILOT DATA: input export does not exist", file=sys.stderr)
        return 2
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != "16.1":
            raise ValueError("schema_version must be 16.1")
        result = analyze_records(payload.get("sessions", []))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"NO PILOT DATA: invalid anonymized export ({exc})", file=sys.stderr)
        return 2
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
