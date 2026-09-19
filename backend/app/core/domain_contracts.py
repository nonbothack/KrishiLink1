"""Shared lifecycle contracts for domain state transitions."""

from collections.abc import Mapping, Set

LOT_TRANSITIONS: Mapping[str, Set[str]] = {
    "DRAFT": frozenset({"PUBLISHED", "CANCELLED"}),
    "PUBLISHED": frozenset({"PARTIALLY_ALLOCATED", "RESERVED", "SOLD", "EXPIRED", "CANCELLED"}),
    "PARTIALLY_ALLOCATED": frozenset({"PARTIALLY_ALLOCATED", "RESERVED", "SOLD", "EXPIRED", "CANCELLED"}),
    "RESERVED": frozenset({"PARTIALLY_ALLOCATED", "SOLD", "EXPIRED", "CANCELLED"}),
    "SOLD": frozenset(),
    "FULFILLED": frozenset(),
    "EXPIRED": frozenset(),
    "CANCELLED": frozenset(),
}

OFFER_TRANSITIONS: Mapping[str, Set[str]] = {
    "PENDING": frozenset({"COUNTERED", "ACCEPTED", "REJECTED", "EXPIRED", "CANCELLED"}),
    # Re-countering is a negotiation event on a parent that remains COUNTERED;
    # each response is a new child offer in the chain.
    "COUNTERED": frozenset({"COUNTERED", "ACCEPTED", "REJECTED", "EXPIRED", "CANCELLED"}),
    "ACCEPTED": frozenset(),
    "REJECTED": frozenset(),
    "EXPIRED": frozenset(),
    "CANCELLED": frozenset(),
}

TRADE_TRANSITIONS: Mapping[str, Set[str]] = {
    # A participant-entered payment reference is evidence of a statement, not
    # settlement. PAYMENT_CONFIRMED is reserved for a future trusted provider
    # boundary and is intentionally not reachable through participant routes.
    "CREATED": frozenset({"PAYMENT_PENDING", "CANCELLED", "DISPUTED"}),
    "PAYMENT_PENDING": frozenset({"CANCELLED", "DISPUTED"}),
    "PAYMENT_CONFIRMED": frozenset({"PROCESSING", "READY_FOR_DISPATCH", "CANCELLED", "DISPUTED"}),
    "PROCESSING": frozenset({"READY_FOR_DISPATCH", "CANCELLED", "DISPUTED"}),
    "READY_FOR_DISPATCH": frozenset({"IN_TRANSIT", "CANCELLED", "DISPUTED"}),
    "IN_TRANSIT": frozenset({"DELIVERED", "DISPUTED"}),
    "DELIVERED": frozenset({"COMPLETED", "DISPUTED"}),
    "DISPUTED": frozenset({"COMPLETED", "CANCELLED", "REFUNDED"}),
    "COMPLETED": frozenset(),
    "CANCELLED": frozenset(),
    "REFUNDED": frozenset(),
}

GRIEVANCE_TRANSITIONS: Mapping[str, Set[str]] = {
    "OPEN": frozenset({"UNDER_REVIEW", "RESOLVED", "REJECTED", "ESCALATED"}),
    "UNDER_REVIEW": frozenset({"RESOLVED", "REJECTED", "ESCALATED"}),
    "ESCALATED": frozenset({"UNDER_REVIEW", "RESOLVED", "REJECTED"}),
    "RESOLVED": frozenset(),
    "REJECTED": frozenset(),
}

STORAGE_BOOKING_TRANSITIONS: Mapping[str, Set[str]] = {
    "REQUESTED": frozenset({"CONFIRMED", "REJECTED", "CANCELLED"}),
    "CONFIRMED": frozenset({"CHECKED_IN", "CANCELLED"}),
    "CHECKED_IN": frozenset({"CHECKED_OUT", "DISPUTED"}),
    "CHECKED_OUT": frozenset(),
    "REJECTED": frozenset(),
    "CANCELLED": frozenset(),
    "DISPUTED": frozenset(),
}

VERIFICATION_CASE_TRANSITIONS: Mapping[str, Set[str]] = {
    "PENDING": frozenset({"IN_REVIEW", "NEEDS_INFORMATION", "APPROVED", "REJECTED", "WITHDRAWN"}),
    "IN_REVIEW": frozenset({"NEEDS_INFORMATION", "APPROVED", "REJECTED"}),
    "NEEDS_INFORMATION": frozenset({"PENDING", "IN_REVIEW", "WITHDRAWN"}),
    "APPROVED": frozenset(),
    "REJECTED": frozenset(),
    "WITHDRAWN": frozenset(),
}

PAYMENT_ATTEMPT_TRANSITIONS: Mapping[str, Set[str]] = {
    "PENDING": frozenset({"SUBMITTED", "FAILED"}),
    "SUBMITTED": frozenset({"SUCCEEDED", "FAILED", "UNKNOWN"}),
    "UNKNOWN": frozenset({"SUCCEEDED", "FAILED", "MANUAL_REVIEW"}),
    "FAILED": frozenset({"RETRY_WAIT", "MANUAL_REVIEW"}),
    "RETRY_WAIT": frozenset({"SUBMITTED"}),
    "SUCCEEDED": frozenset(),
    "MANUAL_REVIEW": frozenset(),
}

NOTIFICATION_ATTEMPT_TRANSITIONS: Mapping[str, Set[str]] = {
    "PENDING": frozenset({"SUBMITTED", "FAILED"}),
    "SUBMITTED": frozenset({"DELIVERED", "FAILED", "UNKNOWN"}),
    "UNKNOWN": frozenset({"DELIVERED", "FAILED", "MANUAL_REVIEW"}),
    "FAILED": frozenset({"RETRY_WAIT", "MANUAL_REVIEW"}),
    "RETRY_WAIT": frozenset({"SUBMITTED"}),
    "DELIVERED": frozenset(),
    "MANUAL_REVIEW": frozenset(),
}


def transition_allowed(current: str | None, target: str, graph: Mapping[str, Set[str]]) -> bool:
    """Return whether a transition is explicitly allowed; terminal/unknown states fail closed."""
    return target.upper() in graph.get((current or "").upper(), frozenset())
