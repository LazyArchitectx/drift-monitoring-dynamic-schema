"""The pre-compute guard — the fix that prevents the freeze.

Before the expensive drift computation runs, this cheap check asks: does the live
upstream schema still match the schema the baseline was built for? If not, it
regenerates the baseline for the live schema FIRST. This is the whole lesson in
one function: validate the cheap thing (schema compatibility) before running the
expensive thing (full drift eval), so an upstream change can never make every
nightly run fail against a stale baseline.
"""

from __future__ import annotations

from driftmon.schema import GuardResult
from driftmon.sources import BaselineStore, SchemaSource


def pre_compute_guard(source: SchemaSource, store: BaselineStore) -> GuardResult:
    live = source.fetch()
    baseline_version = store.current_version()

    if baseline_version != live.version:
        # Schema moved (or no baseline yet) -> regenerate for the live schema first.
        store.regenerate(live)
        return GuardResult(
            schema_stable=False,
            live_version=live.version,
            baseline_version=baseline_version or "(none)",
            action="baseline_regenerated",
        )

    return GuardResult(
        schema_stable=True,
        live_version=live.version,
        baseline_version=baseline_version,
        action="schema_stable",
    )
