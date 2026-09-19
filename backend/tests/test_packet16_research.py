from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[2] / "scripts" / "analyze_pilot_sessions.py"
SPEC = importlib.util.spec_from_file_location("packet16_analysis", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_no_sessions_is_explicitly_not_pilot_evidence():
    result = MODULE.analyze_records([])
    assert result == {
        "status": "NO_PILOT_DATA",
        "n": 0,
        "reason": "No anonymized participant sessions were supplied.",
    }


def test_malformed_session_is_rejected_instead_of_filled_in():
    with pytest.raises(ValueError, match="unsupported role"):
        MODULE.analyze_records(
            [{"session_id": "S16-1", "participant_code": "P16-1", "role": "unknown", "build": "rc", "tasks": []}]
        )


def test_analysis_preserves_denominators_and_requires_unassisted_success():
    result = MODULE.analyze_records(
        [
            {
                "session_id": "S16-1",
                "participant_code": "P16-1",
                "role": "farmer",
                "build": "rc",
                "tasks": [
                    {"task_id": "PRICE", "outcome": "SUCCESS", "elapsed_ms": 1200, "assistance": "NONE", "comprehension": "PASS"},
                    {"task_id": "SELL", "outcome": "SUCCESS", "elapsed_ms": 2200, "assistance": "PROMPT"},
                ],
            },
            {
                "session_id": "S16-2",
                "participant_code": "P16-2",
                "role": "farmer",
                "build": "rc",
                "tasks": [
                    {"task_id": "PRICE", "outcome": "FAIL", "elapsed_ms": 1800, "assistance": "NONE", "comprehension": "FAIL"}
                ],
            },
        ]
    )
    assert result["status"] == "ANALYZED"
    assert result["n"] == 2
    price = result["tasks"]["farmer"]["PRICE"]["success_without_assistance"]
    assert price == {"count": 1, "n": 2, "rate": 0.5}
    assert result["tasks"]["farmer"]["PRICE"]["timing_ms"]["median"] == 1500
    assert "overall_score" not in result
