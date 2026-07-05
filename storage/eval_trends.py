"""Eval trend store: keep every eval run so the dashboard can chart quality
over time (is hallucination/drift creeping up release after release?).

Two backends behind one interface (picked by `settings.trends_mode`):
- sim  : JSON-file shim (out/eval_trends.json) — no GCP, never blocked on creds.
- real : a BigQuery table (settings.bq_dataset.bq_table) appended one row per run.

Each row is the EvalResult flattened plus a timestamp.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from shared.config import settings
from shared.logging import get_logger
from shared.models import EvalResult

log = get_logger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "out" / "eval_trends.json"


def _row(result: EvalResult) -> dict:
    """Flatten one run into a trend row (newest-orderable by ts)."""
    return {"ts": datetime.now(timezone.utc).isoformat(), **result.model_dump(mode="json")}


class EvalTrends(ABC):
    name: str

    @abstractmethod
    def append(self, result: EvalResult) -> None:
        """Record one eval run."""

    @abstractmethod
    def recent(self, suite: str | None = None, limit: int = 50) -> list[dict]:
        """Recent trend rows, newest first; optionally filtered to one suite."""


class JsonFileTrends(EvalTrends):
    """JSON-file shim. Whole file is a list of trend rows. NOTE: append is a
    non-atomic read-modify-write — fine for the single-writer demo/service; the
    real path is BigQuery."""

    name = "json"

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.trends_path or _DEFAULT_PATH)

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8") or "[]")

    def append(self, result: EvalResult) -> None:
        rows = self._load()
        rows.append(_row(result))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        log.info("trends(json) appended run for %s", result.suite)

    def recent(self, suite: str | None = None, limit: int = 50) -> list[dict]:
        rows = self._load()
        if suite is not None:
            rows = [r for r in rows if r.get("suite") == suite]
        rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
        return rows[:limit]


class BigQueryTrends(EvalTrends):
    """BigQuery-backed trends. Lazy client so sim never touches GCP."""

    name = "bigquery"

    def __init__(self) -> None:
        from google.cloud import bigquery  # lazy: only when trends_mode=real

        self._client = bigquery.Client(project=settings.google_cloud_project or None)
        self._table = f"{settings.bq_dataset}.{settings.bq_table}"

    def append(self, result: EvalResult) -> None:
        errors = self._client.insert_rows_json(self._table, [_row(result)])
        if errors:
            raise RuntimeError(f"BigQuery insert failed: {errors}")
        log.info("trends(bigquery) appended run for %s", result.suite)

    def recent(self, suite: str | None = None, limit: int = 50) -> list[dict]:
        where = "WHERE suite = @suite" if suite is not None else ""
        from google.cloud import bigquery

        params = (
            [bigquery.ScalarQueryParameter("suite", "STRING", suite)]
            if suite is not None
            else []
        )
        job = self._client.query(
            f"SELECT * FROM `{self._table}` {where} ORDER BY ts DESC LIMIT {int(limit)}",
            job_config=bigquery.QueryJobConfig(query_parameters=params),
        )
        return [dict(r) for r in job.result()]


def get_trends(mode: str | None = None) -> EvalTrends:
    """Factory: JSON shim (sim) or BigQuery (real), by trends_mode."""
    chosen = mode or settings.trends_mode
    if chosen == "real":
        return BigQueryTrends()
    return JsonFileTrends()
