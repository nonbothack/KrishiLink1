"""Create an internal, reproducible release-candidate snapshot manifest.

This intentionally records dirty state instead of pretending the working tree
is a tagged release. It contains hashes and build metadata only; no secrets or
file contents are emitted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "release" / "release-candidate-manifest.json"


def run(*args: str) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hashes(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        str(file.relative_to(ROOT)).replace("\\", "/"): digest(file.read_bytes())
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def migration_head() -> str:
    versions = ROOT / "backend" / "alembic" / "versions"
    revisions: set[str] = set()
    parents: set[str] = set()
    for file in versions.glob("*.py"):
        text = file.read_text(encoding="utf-8", errors="replace")
        rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)", text, re.MULTILINE)
        if rev:
            revisions.add(rev.group(1))
        parent = re.search(r"^down_revision\s*=\s*['\"]([^'\"]+)", text, re.MULTILINE)
        if parent:
            parents.add(parent.group(1))
    heads = sorted(revisions - parents)
    return ",".join(heads) if heads else "unavailable"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    status = run("git", "status", "--porcelain=v1", "--untracked-files=all")
    manifest = {
        "schema_version": 1,
        "candidate_label": "UNCOMMITTED_RELEASE_CANDIDATE_SNAPSHOT",
        "candidate_version": os.getenv("RELEASE_VERSION", "2.0.0-rc.15"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": run("git", "branch", "--show-current"),
        "head_sha": run("git", "rev-parse", "HEAD"),
        "working_tree_dirty": bool(status),
        "tracked_diff_sha256": digest(run("git", "diff", "--no-ext-diff").encode()),
        "staged_diff_sha256": digest(run("git", "diff", "--cached", "--no-ext-diff").encode()),
        "status_sha256": digest(status.encode()),
        "frontend_artifact_sha256": file_hashes(ROOT / "frontend" / "dist"),
        "backend_dependency_lock_sha256": file_hashes(ROOT / "backend" / "requirements.txt"),
        "frontend_dependency_lock_sha256": file_hashes(ROOT / "frontend" / "package-lock.json"),
        "migration_head": migration_head(),
        "environment_profile": os.getenv("RELEASE_ENV_PROFILE", "local-release-candidate"),
        "source_of_truth": "docs/release/production-readiness.md",
    }
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
