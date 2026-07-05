"""Export the AI Quality Gate decision as a committed demo artifact.

Deterministic and offline: runs the sim eval backend (no Gemini, no creds) for a
clean release and a regressed release, then writes both gate decisions to
out/eval_gate.md. This is the P3 definition-of-done artifact — the gate visibly
passing one deploy and blocking another.

    python scripts/export_eval_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.sentinel.pillars.ai_quality_gate.gate import run_gate  # noqa: E402
from shared.models import Signal  # noqa: E402

_OUT = Path(__file__).resolve().parent.parent / "out" / "eval_gate.md"
_SUITES = ("checkout-llm-v1", "checkout-llm-v2")  # clean release, then regressed


def _render_decision(signal: Signal) -> str:
    d = signal.detail
    verdict = "✅ PASS" if signal.status == "ok" else "🔴 BLOCKED"
    return (
        f"## {d['suite']} — {verdict}\n\n"
        f"{signal.headline}\n\n"
        f"| Metric | Value | Threshold |\n"
        f"|---|---|---|\n"
        f"| Hallucination rate | {d['hallucination_rate']:.0%} | {d['threshold']:.0%} |\n"
        f"| Drift | {d['drift']:.0%} | {d['threshold']:.0%} |\n"
        f"| Gate passed | {d['passed']} | — |\n"
    )


def main() -> None:
    sections = [_render_decision(run_gate(suite, mode="sim")) for suite in _SUITES]
    body = (
        "# AI Quality Gate — Decisions\n\n"
        "The gate blocks a deploy when an LLM release regresses past the quality "
        "threshold (hallucination or drift). Two sim runs below: a clean release "
        "ships, a regressed one is blocked.\n\n"
        + "\n".join(sections)
    )
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(body, encoding="utf-8")
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
