"""Plain-English CI failure root cause for an MR.

The pipeline-logs adapter call returns the raw log tail; Gemini turns it into one
paragraph fit for an MR comment. Returns None when CI is green (nothing to
explain), so the caller can leave MRReview.ci_root_cause unset.
"""

from __future__ import annotations

from integrations.gitlab.factory import get as get_gitlab
from shared.llm import generate
from shared.logging import get_logger

from .prompt import CI_RCA_INSTRUCTION

log = get_logger(__name__)


def diagnose_ci(mr_id: int) -> str | None:
    """Pull the pipeline logs for `mr_id` and return a plain-English RCA.

    Returns None if:
      - the adapter has no record of the MR, or
      - the pipeline status is anything other than `failed` (nothing to explain).
    """
    payload = get_gitlab().get_pipeline_logs(mr_id)
    if "error" in payload:
        log.info("no pipeline for MR %s; skipping CI RCA", mr_id)
        return None
    if payload.get("status") != "failed":
        log.info("pipeline for MR %s is %s; skipping CI RCA", mr_id, payload.get("status"))
        return None

    prompt = (
        f"{CI_RCA_INSTRUCTION}\n\n"
        f"FAILED JOB: {payload.get('failed_job')}\n"
        f"PIPELINE ID: {payload.get('pipeline_id')}\n\n"
        f"LOG TAIL:\n{payload['logs']}"
    )
    text = generate(prompt).strip()
    return text or None
