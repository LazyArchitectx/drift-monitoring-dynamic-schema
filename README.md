# Drift Monitoring with Dynamic Schema Ingestion

A drift monitor that **can't be broken by an upstream schema change.** A cheap
pre-compute guard checks whether the live tool schema still matches the schema the
ground-truth baseline was built for — and regenerates the baseline first if it drifted —
so an upstream change can never silently make every nightly run fail against a stale
baseline.

[![ci](https://github.com/LazyArchitectx/drift-monitoring-dynamic-schema/actions/workflows/ci.yml/badge.svg)](https://github.com/LazyArchitectx/drift-monitoring-dynamic-schema/actions)

> **What this is.** A portfolio demonstrator built around a real failure mode and its fix:
> a drift monitor froze every nightly release because a static ground-truth baseline went
> stale after an upstream schema change — the model was correct, the baseline was old. This
> repo implements the *fixed* system and shows the failure it prevents. Clean, from-scratch,
> not a proprietary system.

---

## The failure this prevents

```
BEFORE (the incident):
  upstream team changes a tool schema
      -> static ground-truth baseline is now stale
      -> drift monitor grades CORRECT outputs against an OLD baseline
      -> every nightly run fails -> deployment freeze

AFTER (this repo):
  a cheap guard checks: does the live schema match the baseline's schema?
      -> if not, regenerate the baseline for the live schema FIRST
      -> then run drift -> a failure now means REAL drift, not a stale baseline
```

## The one idea

**Ground truth is a dependency with a change feed, not a static asset.** Baselines are
tagged with the schema version they were built for and stored per-version. Before the
expensive drift computation runs, the guard compares the live schema to the baseline's
schema — validate the cheap thing before the expensive thing.

## Architecture

```
   SchemaSource ─► pre_compute_guard ─► live schema == baseline schema ?
   (upstream)          (cheap)               ├─ yes ─► run drift monitor (PSI)
                                             └─ no  ─► regenerate baseline for
                                                       the live schema, THEN drift
```

`SchemaSource` and `BaselineStore` are small swappable classes — replace the in-memory
versions with an HTTP registry and an S3 store without touching the guard or monitor.

## Quickstart

```bash
pip install -e ".[dev]"
driftmon-demo
```

Output — run 2 is the incident scenario, absorbed:

```json
{"run": 1, "guard": "schema_stable", "drift_detected": false}
{"run": 2, "schema_changed": "v1->v2", "guard": "baseline_regenerated", "drift_detected": false}
{"summary": "schema change absorbed by the guard; no false freeze"}
```

## Testing

```bash
ruff check .     # lint
pytest -v        # 5 tests
```

The key test is `test_schema_change_does_not_cause_false_drift`: it reproduces the exact
incident — an upstream schema change with unchanged model behavior — and asserts the guard
regenerates the baseline so drift is (correctly) **not** detected. Without the guard, that
run would falsely freeze.

## Project layout

```
src/driftmon/
  schema.py       ToolSchema, Baseline, GuardResult, DriftResult
  sources.py      SchemaSource + BaselineStore (swappable dependencies)
  guard.py        pre_compute_guard — the fix
  monitor.py      check_drift — PSI vs the version-matched baseline
  cli.py          driftmon-demo — the two-run scenario
tests/            guard, monitor, and the false-freeze-prevention test
docs/DESIGN.md    deeper architecture + the incident write-up
```

## What I'd build next

- Real adapters: an HTTP `SchemaSource` and an S3-backed `BaselineStore`.
- Alerting on genuine drift (only after the guard confirms schemas match).
- A schema-diff report, so a regeneration explains what upstream actually changed.

## License

MIT — see [LICENSE](LICENSE).
