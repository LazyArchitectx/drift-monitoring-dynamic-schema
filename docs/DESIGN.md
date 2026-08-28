# Design Notes

Rationale behind the drift monitor — written to be defended in a technical interview.

## Why the guard runs BEFORE the drift computation

The failure this project prevents happened because a static ground-truth baseline was
compared against current outputs without ever checking whether the *baseline itself* was
still valid. The fix isn't a smarter drift metric — it's a cheap sanity check that runs
first: does the live upstream schema still match the schema the baseline was built for?
This ordering (validate the cheap thing before the expensive thing) is the entire lesson,
generalized: any pipeline stage that depends on an external assumption should check that
assumption before spending compute on the expensive stage built on top of it.

## Why ground truth is treated as a dependency, not an asset

The original incident happened because the baseline was implicitly assumed to be
permanent. Tagging every baseline with the schema version it was built for, and storing
baselines per-version, makes the dependency explicit and inspectable — a baseline is now
data with a stated validity condition, not a fact taken for granted.

## Why SchemaSource and BaselineStore are separate, swappable classes

Neither the guard nor the monitor cares whether the schema comes from an HTTP registry or
an in-memory stub, or whether the baseline lives in S3 or a dict. Keeping them behind small
classes means the demo and tests run fully offline and deterministically, while a
production deployment swaps in real adapters without touching the guard or monitor logic
at all. This is the same dependency-inversion pattern used in the other four projects in
this portfolio (Judge Protocol, Agent Protocol, check registry, gate policy) — the seam
that makes each system testable without external calls.

## Why the regenerated baseline uses the SAME comparison logic afterward

Once the guard regenerates a baseline for the new schema version, the drift check that
follows is unchanged — same PSI computation, same tolerance. This is deliberate: the fix
is entirely in *making sure the comparison is apples-to-apples*, not in changing what
"drift" means. A failure after the guard has run is trustworthy specifically because the
guard already ruled out "stale baseline" as the cause.

## The test that proves the fix

`test_schema_change_does_not_cause_false_drift` reproduces the exact incident: an upstream
schema change with model behavior held constant. Without the guard, comparing unchanged
correct outputs against a v1 baseline under a v2 schema would show drift; the guard
regenerates the baseline for v2 first, and the test asserts drift is correctly NOT
detected. That single assertion is the whole story about the incident, in code.

## Scope and honesty

This is a from-scratch demonstrator of the pattern behind a real incident and its fix, not
a reproduction of any proprietary monitoring system. A production version would add real
adapters (an HTTP schema registry, an S3-backed baseline store), alerting, and a
schema-diff report — named in the README's "What I'd build next".
