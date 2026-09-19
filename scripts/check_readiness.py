"""Low-complexity consistency check for the Packet 14 evidence pack.

This script checks repository evidence references and explicit claim wording. It
does not decide legal compliance, certification, resilience or production
readiness.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/readiness/readiness-manifest.json"
FORBIDDEN_CLAIMS = re.compile(r"\b(?:GIGW compliant|STQC certified|CERT-In compliant|DPDP compliant|ISO compliant|production ready)\b", re.IGNORECASE)


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.exists():
        errors.append(f"missing {MANIFEST}")
    else:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("certification_claim") is not False:
            errors.append("readiness manifest must set certification_claim=false")
        for control in manifest.get("controls", []):
            evidence = ROOT / control["evidence"]
            if not evidence.exists():
                errors.append(f"{control['id']} evidence missing: {control['evidence']}")
            if control.get("status") == "IMPLEMENTED_AND_TESTED" and not control.get("evidence"):
                errors.append(f"{control['id']} has tested status without evidence")

    for path in (ROOT / "docs/readiness").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        # Allow the exact negated wording used by the readiness rules, but flag
        # unqualified positive claims in evidence artifacts.
        for match in FORBIDDEN_CLAIMS.finditer(text):
            line = text[text.rfind("\n", 0, match.start()) + 1:text.find("\n", match.end())].lower()
            if "do not" not in line and "not" not in line and "no " not in line:
                errors.append(f"unqualified certification claim in {path}: {match.group(0)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Packet 14 readiness evidence checks passed (no legal/certification conclusion made).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
