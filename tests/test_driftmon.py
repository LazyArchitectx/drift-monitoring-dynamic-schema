"""Tests: the guard catches schema changes, and the fix prevents the false freeze."""

from driftmon.guard import pre_compute_guard
from driftmon.monitor import check_drift
from driftmon.schema import Baseline, ToolSchema
from driftmon.sources import BaselineStore, SchemaSource


def _generator():
    def generate(schema: ToolSchema) -> Baseline:
        return Baseline(schema_version=schema.version, scores=[0.5] * 20)

    return generate


def test_guard_stable_when_schema_matches():
    source = SchemaSource(ToolSchema(version="v1"))
    store = BaselineStore(_generator())
    store.seed(Baseline(schema_version="v1", scores=[0.5] * 20))
    result = pre_compute_guard(source, store)
    assert result.schema_stable is True
    assert result.action == "schema_stable"


def test_guard_regenerates_when_schema_changes():
    source = SchemaSource(ToolSchema(version="v1"))
    store = BaselineStore(_generator())
    store.seed(Baseline(schema_version="v1", scores=[0.5] * 20))
    source.set_schema(ToolSchema(version="v2"))  # upstream change
    result = pre_compute_guard(source, store)
    assert result.schema_stable is False
    assert result.action == "baseline_regenerated"
    assert store.get("v2") is not None  # a v2 baseline now exists


def test_drift_detected_on_real_shift():
    baseline = Baseline(schema_version="v1", scores=[0.1] * 20)
    result = check_drift([0.9] * 20, baseline)  # genuinely different distribution
    assert result.drift_detected is True


def test_no_drift_when_distribution_matches():
    baseline = Baseline(schema_version="v1", scores=[0.5] * 20)
    result = check_drift([0.5] * 20, baseline)
    assert result.drift_detected is False


def test_schema_change_does_not_cause_false_drift():
    """The core failure this project prevents: a schema change must NOT freeze the run.

    Without the guard, run 2 would compare correct outputs against a v1 baseline and
    falsely detect drift. With the guard, the baseline is regenerated for v2 first, so
    the comparison is clean and drift is (correctly) not detected.
    """
    source = SchemaSource(ToolSchema(version="v1"))
    store = BaselineStore(_generator())
    store.seed(Baseline(schema_version="v1", scores=[0.5] * 20))

    source.set_schema(ToolSchema(version="v2"))
    guard = pre_compute_guard(source, store)          # regenerates v2 baseline
    baseline_v2 = store.get("v2")
    drift = check_drift([0.5] * 20, baseline_v2)       # model behavior unchanged

    assert guard.action == "baseline_regenerated"
    assert drift.drift_detected is False               # no false freeze
