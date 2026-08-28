"""Validated models for schema versions, guard results, and drift results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolSchema(BaseModel):
    """A versioned upstream tool schema. `version` is what the baseline pins to."""

    version: str
    fields: list[str] = Field(default_factory=list)


class Baseline(BaseModel):
    """A ground-truth baseline, tagged with the schema version it was built for.

    The whole failure this project prevents comes from a baseline whose schema_version
    silently falls behind the live schema.
    """

    schema_version: str
    scores: list[float] = Field(default_factory=list)


class GuardResult(BaseModel):
    """Outcome of the cheap pre-compute schema check."""

    schema_stable: bool
    live_version: str
    baseline_version: str
    action: str  # "schema_stable" | "baseline_regenerated"


class DriftResult(BaseModel):
    """Outcome of the drift comparison (only meaningful once schemas match)."""

    psi: float
    tolerance: float
    drift_detected: bool
    schema_version: str
