"""Command-line demo of the guard-then-monitor pipeline.

It runs a small scripted scenario end to end (no external services), showing:
  1. a stable run (schema unchanged, drift computed normally), and
  2. the failure scenario the fix prevents: the upstream schema changes, the guard
     catches it and regenerates the baseline BEFORE the drift eval, so the run does
     not falsely fail.

    driftmon-demo
"""

from __future__ import annotations

import argparse
import json

from driftmon.guard import pre_compute_guard
from driftmon.monitor import check_drift
from driftmon.schema import Baseline, ToolSchema
from driftmon.sources import BaselineStore, SchemaSource


def _make_generator():
    # Ground-truth generator: a real system re-derives baselines; here we return a
    # stable reference distribution tagged with whatever schema is current.
    def generate(schema: ToolSchema) -> Baseline:
        return Baseline(schema_version=schema.version, scores=[0.5] * 20)

    return generate


def _run(_args: argparse.Namespace) -> int:
    source = SchemaSource(ToolSchema(version="v1", fields=["a", "b"]))
    store = BaselineStore(_make_generator())
    store.seed(Baseline(schema_version="v1", scores=[0.5] * 20))

    # --- Run 1: schema stable -> normal drift check ---
    guard1 = pre_compute_guard(source, store)
    baseline = store.get(source.fetch().version)
    drift1 = check_drift([0.5] * 20, baseline)
    print(json.dumps({"run": 1, "guard": guard1.action, "drift_detected": drift1.drift_detected}))

    # --- Run 2: upstream changes the schema (the incident trigger) ---
    source.set_schema(ToolSchema(version="v2", fields=["a", "b", "c"]))
    guard2 = pre_compute_guard(source, store)  # catches the change, regenerates baseline
    baseline2 = store.get(source.fetch().version)
    # model behavior is unchanged/correct; without the guard this would falsely fail
    drift2 = check_drift([0.5] * 20, baseline2)
    print(
        json.dumps(
            {
                "run": 2,
                "schema_changed": "v1->v2",
                "guard": guard2.action,          # baseline_regenerated
                "drift_detected": drift2.drift_detected,  # False — no false alarm
            }
        )
    )
    print(json.dumps({"summary": "schema change absorbed by the guard; no false freeze"}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="driftmon-demo", description=__doc__)
    parser.set_defaults(func=_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
