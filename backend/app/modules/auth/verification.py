"""Evidence-based external business and bank verification boundaries."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VerificationOutcome:
    status: str
    method: str | None = None
    provider: str | None = None
    provider_reference: str | None = None
    reason_code: str | None = None


class BusinessVerificationProvider(Protocol):
    def verify(self, registration_reference: str) -> VerificationOutcome: ...


class BankVerificationProvider(Protocol):
    def verify(self, account_reference: str) -> VerificationOutcome: ...


class UnconfiguredBusinessVerificationProvider:
    def verify(self, registration_reference: str) -> VerificationOutcome:
        del registration_reference
        return VerificationOutcome(status="UNAVAILABLE", reason_code="provider_unconfigured")


class UnconfiguredBankVerificationProvider:
    def verify(self, account_reference: str) -> VerificationOutcome:
        del account_reference
        return VerificationOutcome(status="UNAVAILABLE", reason_code="provider_unconfigured")
