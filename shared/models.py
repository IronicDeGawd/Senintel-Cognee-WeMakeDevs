"""THE CONTRACT. Pydantic models every pillar and the dashboard import.

Frozen after the pairing hour — APPEND-ONLY. Adding a new optional field is
fine; renaming/removing/retyping an existing field breaks every consumer.

Mental model: each pillar does its own work, then emits a `Signal` (the common
envelope). The dashboard only ever speaks `Signal`. The pillar-specific payload
(Incident / MRReview / EvalResult) rides inside `Signal.detail`.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Problem(BaseModel):
    """P2 in — mirrors one Dynatrace `list_problems` entry (Davis anomaly)."""

    problem_id: str
    title: str
    severity: Severity
    status: str
    service: str
    root_cause_entity: str | None = None
    start_time: datetime
    evidence: dict


class Finding(BaseModel):
    """P1 in — one code-review issue raised against a diff."""

    file: str
    line: int | None = None
    category: str
    severity: Severity
    message: str
    suggestion: str | None = None


class MRReview(BaseModel):
    """P1 out — the full review of a merge request."""

    mr_id: int
    commit: str
    findings: list[Finding]
    ci_root_cause: str | None = None


class EvalResult(BaseModel):
    """P3 out — outcome of one eval suite run."""

    suite: str
    hallucination_rate: float
    drift: float
    passed: bool
    threshold: float


class Incident(BaseModel):
    """P2 out — the briefing artifact (one correlated incident)."""

    title: str
    severity: Severity
    service: str
    summary: str
    suspected_cause: str
    suspect_commit: str | None = None
    next_action: str


class Signal(BaseModel):
    """THE DASHBOARD CONTRACT — every pillar emits this envelope."""

    pillar: Literal["code", "production", "ai_quality"]
    status: Literal["ok", "warning", "critical"]
    headline: str
    detail: dict  # pillar-specific payload (Incident / MRReview / EvalResult)
    ts: datetime
