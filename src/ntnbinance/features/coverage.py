"""Coverage gates for optional point-in-time context datasets."""

from __future__ import annotations

from ntnbinance.features.models import (
    CoverageDecision,
    CoverageEvidence,
    CoverageGateResult,
)


def evaluate_coverage(
    evidence: CoverageEvidence, *, minimum_percent: float, minimum_span_days: int
) -> CoverageGateResult:
    if not 0 <= minimum_percent <= 100 or minimum_span_days < 1:
        raise ValueError("invalid coverage threshold")
    reasons: list[str] = []
    if evidence.expected <= 0 or evidence.actual < 0 or evidence.actual > evidence.expected:
        reasons.append("INVALID_COUNTS")
    if evidence.percentage < minimum_percent:
        reasons.append("COVERAGE_BELOW_THRESHOLD")
    if evidence.span_days < minimum_span_days:
        reasons.append("HISTORY_SPAN_TOO_SHORT")
    return CoverageGateResult(
        dataset=evidence.dataset,
        decision=CoverageDecision.EXCLUDE if reasons else CoverageDecision.INCLUDE,
        percentage=evidence.percentage,
        span_days=evidence.span_days,
        reason_codes=tuple(reasons),
    )
