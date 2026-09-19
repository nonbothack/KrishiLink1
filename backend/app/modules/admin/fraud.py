"""Deterministic fraud/risk signals. Signals create review work, not convictions."""

from sqlalchemy.orm import Session

from app.models import FraudCase


def record_signal(
    db: Session,
    *,
    subject_type: str,
    subject_id: str,
    signal_type: str,
    rule_id: str,
    rule_version: str,
    severity: str,
    evidence_refs: list[str],
) -> FraudCase:
    """Create one case per subject/signal/rule version and return the existing case on retry."""
    existing = db.query(FraudCase).filter(
        FraudCase.subject_type == subject_type,
        FraudCase.subject_id == subject_id,
        FraudCase.signal_type == signal_type,
        FraudCase.rule_version == rule_version,
    ).first()
    if existing:
        return existing
    case = FraudCase(
        subject_type=subject_type,
        subject_id=subject_id,
        signal_type=signal_type,
        rule_id=rule_id,
        rule_version=rule_version,
        severity=severity,
        evidence_refs=evidence_refs,
    )
    db.add(case)
    db.flush()
    return case
