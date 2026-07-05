"""Run one AI Quality Gate cycle from the CLI and print the result.

    python scripts/run_eval_gate.py                      # default: checkout-llm-v2 (regressed)
    python scripts/run_eval_gate.py checkout-llm-v1      # a clean release

Gemini generates an adversarial eval suite for the change (one live call), then
the suite is run through the eval backend (SENTINEL_ARIZE_MODE, sim by default)
and gated. Prints the generated suite and the emitted Signal.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.sentinel.pillars.ai_quality_gate.evalgen import generate_eval_suite  # noqa: E402
from agents.sentinel.pillars.ai_quality_gate.gate import run_gate  # noqa: E402

_DEFAULT_CHANGE = (
    "checkout-llm: a support assistant that explains order and refund issues to "
    "shoppers. The change swaps in a new system prompt that summarizes the order "
    "timeline and suggests next steps."
)


def main() -> None:
    suite = sys.argv[1] if len(sys.argv) > 1 else "checkout-llm-v2"
    generated = generate_eval_suite(_DEFAULT_CHANGE, suite)
    print(f"generated {len(generated.cases)} adversarial case(s) for {suite}:")
    for case in generated.cases:
        print(f"  [{case.category}] {case.prompt}")

    signal = run_gate(suite)
    print("\n--- gate decision ---")
    print(signal.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
