"""The upstream schema source and the baseline store.

Both are behind small classes so they can be swapped for real implementations (an
HTTP registry, an S3 bucket) without touching the guard or monitor logic. The
in-memory versions here make the demo and tests run offline and deterministically.
"""

from __future__ import annotations

from collections.abc import Callable

from driftmon.schema import Baseline, ToolSchema


class SchemaSource:
    """Fetches the CURRENT upstream tool schema. In-memory stand-in for a registry."""

    def __init__(self, schema: ToolSchema) -> None:
        self._schema = schema

    def set_schema(self, schema: ToolSchema) -> None:
        # Simulates an upstream team changing the schema out from under us.
        self._schema = schema

    def fetch(self) -> ToolSchema:
        return self._schema


class BaselineStore:
    """Stores baselines keyed by schema version, and regenerates on demand.

    `generator` builds a fresh baseline for a given schema — in production this
    re-derives ground truth; here it's an injected function so tests control it.
    """

    def __init__(self, generator: Callable[[ToolSchema], Baseline]) -> None:
        self._generator = generator
        self._by_version: dict[str, Baseline] = {}

    def seed(self, baseline: Baseline) -> None:
        self._by_version[baseline.schema_version] = baseline

    def current_version(self) -> str | None:
        if not self._by_version:
            return None
        # the most recently stored baseline's version
        return next(reversed(self._by_version))

    def get(self, version: str) -> Baseline | None:
        return self._by_version.get(version)

    def regenerate(self, schema: ToolSchema) -> Baseline:
        baseline = self._generator(schema)
        self._by_version[schema.version] = baseline
        return baseline
