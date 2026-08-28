"""The drift monitor.

Compares current output scores against the baseline built for the SAME schema
version. Because the guard runs first, this comparison is always apples-to-apples,
so a positive result means real model drift — not a stale-baseline artifact.
"""

from __future__ import annotations

import math

from driftmon.schema import Baseline, DriftResult


def _psi(expected: list[float], actual: list[float], bins: int = 10) -> float:
    lo, hi = min(expected + actual), max(expected + actual)
    if hi == lo:
        return 0.0
    width = (hi - lo) / bins

    def dist(xs: list[float]) -> list[float]:
        counts = [0] * bins
        for x in xs:
            counts[min(int((x - lo) / width), bins - 1)] += 1
        n = len(xs) or 1
        return [c / n for c in counts]

    e, a = dist(expected), dist(actual)
    psi = 0.0
    for ei, ai in zip(e, a):
        ei, ai = ei or 1e-6, ai or 1e-6
        psi += (ai - ei) * math.log(ai / ei)
    return abs(psi)


def check_drift(
    current_scores: list[float], baseline: Baseline, tolerance: float = 0.2
) -> DriftResult:
    psi = _psi(baseline.scores, current_scores)
    return DriftResult(
        psi=round(psi, 4),
        tolerance=tolerance,
        drift_detected=psi > tolerance,
        schema_version=baseline.schema_version,
    )
