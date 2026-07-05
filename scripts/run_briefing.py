"""Run one Production Sentinel cycle from the CLI and print the emitted Signal.

    python scripts/run_briefing.py        # uses SENTINEL_DT_MODE (sim by default)

RCA -> correlation -> KB lookup/save -> deliver (out/briefing.md in sim) -> Signal.
Two live Gemini calls (RCA + correlation).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.sentinel.pillars.production_sentinel.cycle import run_production_cycle  # noqa: E402


def main() -> None:
    signal = run_production_cycle()
    print(signal.model_dump_json(indent=2))
    print(f"\ndelivered briefing -> {signal.detail['delivered_to']}")


if __name__ == "__main__":
    main()
