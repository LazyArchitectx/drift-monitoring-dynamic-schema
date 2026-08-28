"""Drift monitoring with dynamic schema ingestion.

A drift monitor that can't be broken by an upstream schema change. It treats the
ground-truth baseline as a dependency with a change feed, not a static asset: a
cheap pre-compute guard checks whether the live tool schema still matches the
baseline's schema and regenerates the baseline first if it drifted — so an
upstream change can't silently invalidate every nightly run.
"""

from driftmon.guard import pre_compute_guard
from driftmon.monitor import check_drift
from driftmon.schema import DriftResult, GuardResult

__all__ = ["DriftResult", "GuardResult", "check_drift", "pre_compute_guard"]
__version__ = "1.0.0"
