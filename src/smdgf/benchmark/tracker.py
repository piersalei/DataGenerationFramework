"""Local-first benchmark run tracking with optional adapter hooks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

from smdgf.benchmark.models import ArtifactReference, BenchmarkRunManifest, TrackedBenchmarkRun


class TrackingAdapter(Protocol):
    """Optional backend adapter invoked after local persistence succeeds."""

    def record_run(self, tracked_run: TrackedBenchmarkRun) -> None:
        """Record a tracked run in an auxiliary backend."""


class RunTracker(Protocol):
    """Contract for benchmark run tracking implementations."""

    def track_run(
        self,
        manifest: BenchmarkRunManifest,
        *,
        params: dict[str, Any] | None = None,
        metrics: dict[str, float] | None = None,
        tags: dict[str, str] | None = None,
        artifact_refs: Iterable[ArtifactReference] | None = None,
        status: str = "completed",
    ) -> TrackedBenchmarkRun:
        """Persist one benchmark run and return the stored tracking record."""

    def get_run(self, run_id: str) -> TrackedBenchmarkRun:
        """Load one previously tracked run."""

    def list_runs(self) -> list[TrackedBenchmarkRun]:
        """List all tracked runs available to this tracker."""


@dataclass(frozen=True)
class RunComparison:
    """Metric delta summary between two tracked runs."""

    baseline_run_id: str
    candidate_run_id: str
    metric_deltas: dict[str, float]
    baseline_metrics: dict[str, float]
    candidate_metrics: dict[str, float]
    changed_tags: dict[str, tuple[str | None, str | None]]
    artifact_ref_delta: int


class LocalRunTracker:
    """Persist tracked runs as local JSON files and optionally fan out to adapters."""

    def __init__(
        self,
        base_dir: Path,
        *,
        adapters: Iterable[TrackingAdapter] | None = None,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._runs_dir = self._base_dir / "runs"
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._adapters = list(adapters or [])

    def track_run(
        self,
        manifest: BenchmarkRunManifest,
        *,
        params: dict[str, Any] | None = None,
        metrics: dict[str, float] | None = None,
        tags: dict[str, str] | None = None,
        artifact_refs: Iterable[ArtifactReference] | None = None,
        status: str = "completed",
    ) -> TrackedBenchmarkRun:
        """Create or overwrite one local tracking record for the given manifest."""

        tracked_run = TrackedBenchmarkRun(
            run_id=manifest.run_id,
            benchmark_id=manifest.benchmark_id,
            benchmark_manifest_path=manifest.layout.manifest_path,
            params=dict(params or manifest.config_snapshot.values),
            metrics=dict(metrics or manifest.metrics),
            tags=_coerce_tags(tags, manifest.tags),
            artifact_refs=list(artifact_refs or manifest.artifact_refs),
            status=status,
            adapter_metadata={"adapter_count": len(self._adapters)},
        )
        tracked_run.write_json(self._run_path(manifest.run_id))
        for adapter in self._adapters:
            adapter.record_run(tracked_run)
        return tracked_run

    def get_run(self, run_id: str) -> TrackedBenchmarkRun:
        """Load one tracked run from local storage."""

        return TrackedBenchmarkRun.read_json(self._run_path(run_id))

    def list_runs(self) -> list[TrackedBenchmarkRun]:
        """Return all tracked runs in deterministic run-id order."""

        runs = []
        for path in sorted(self._runs_dir.glob("*.json")):
            runs.append(TrackedBenchmarkRun.read_json(path))
        return runs

    def _run_path(self, run_id: str) -> Path:
        return self._runs_dir / f"{run_id}.json"


def compare_runs(
    baseline: TrackedBenchmarkRun,
    candidate: TrackedBenchmarkRun,
) -> RunComparison:
    """Compare two tracked runs without requiring any remote backend."""

    metric_names = sorted(set(baseline.metrics) | set(candidate.metrics))
    metric_deltas = {
        name: candidate.metrics.get(name, 0.0) - baseline.metrics.get(name, 0.0)
        for name in metric_names
    }

    tag_names = sorted(set(baseline.tags) | set(candidate.tags))
    changed_tags = {
        name: (baseline.tags.get(name), candidate.tags.get(name))
        for name in tag_names
        if baseline.tags.get(name) != candidate.tags.get(name)
    }

    return RunComparison(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        metric_deltas=metric_deltas,
        baseline_metrics=dict(baseline.metrics),
        candidate_metrics=dict(candidate.metrics),
        changed_tags=changed_tags,
        artifact_ref_delta=len(candidate.artifact_refs) - len(baseline.artifact_refs),
    )


def load_tracked_runs(base_dir: Path) -> list[TrackedBenchmarkRun]:
    """Convenience helper for tooling that needs all local tracking records."""

    return LocalRunTracker(base_dir).list_runs()


def _coerce_tags(
    explicit_tags: dict[str, str] | None,
    manifest_tags: list[str],
) -> dict[str, str]:
    tags = dict(explicit_tags or {})
    if not manifest_tags:
        return tags

    normalized = [tag for tag in manifest_tags if tag]
    if normalized:
        tags.setdefault("labels", ",".join(normalized))
    return tags


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def dump_comparison(comparison: RunComparison) -> str:
    """Serialize a run comparison for CLI or report rendering."""

    payload = {
        "baseline_run_id": comparison.baseline_run_id,
        "candidate_run_id": comparison.candidate_run_id,
        "metric_deltas": comparison.metric_deltas,
        "baseline_metrics": comparison.baseline_metrics,
        "candidate_metrics": comparison.candidate_metrics,
        "changed_tags": {
            key: list(value) for key, value in comparison.changed_tags.items()
        },
        "artifact_ref_delta": comparison.artifact_ref_delta,
    }
    return json.dumps(payload, indent=2, default=_json_default, sort_keys=True)
