"""Machine-check the release-candidate evidence envelope.

The checker is deliberately conservative: a dirty snapshot is valid evidence
for review, but hard infrastructure blockers keep the candidate from claiming
release readiness.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "release" / "release-candidate-manifest.json"
READINESS = ROOT / "docs" / "release" / "production-readiness.md"
REQUIRED = {
    "schema_version",
    "candidate_label",
    "candidate_version",
    "generated_at",
    "branch",
    "head_sha",
    "working_tree_dirty",
    "tracked_diff_sha256",
    "staged_diff_sha256",
    "frontend_artifact_sha256",
    "backend_dependency_lock_sha256",
    "frontend_dependency_lock_sha256",
    "migration_head",
    "environment_profile",
}


def main() -> int:
    if not MANIFEST.exists() or not READINESS.exists():
        print("release evidence missing")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - manifest.keys())
    if missing:
        print(f"manifest missing keys: {', '.join(missing)}")
        return 1
    if manifest["candidate_label"] != "UNCOMMITTED_RELEASE_CANDIDATE_SNAPSHOT":
        print("candidate label is not the required uncommitted snapshot label")
        return 1
    text = READINESS.read_text(encoding="utf-8")
    if "BLOCKED" not in text:
        print("production-readiness.md must state the current release status")
        return 1
    print("release candidate evidence envelope is structurally valid; release status remains evidence-controlled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
