"""Seed the team's code-review memory into the active backend, then run a recall
smoke so you can see remember -> recall working before the demo.

Backend is chosen by SENTINEL_MEMORY_MODE:
  sim  = offline JSON shim (out/team_memory.json), no creds — good for a dry run.
  real = Cognee Cloud. Set SENTINEL_MEMORY_MODE=real + COGNEE_API_KEY in .env first
         (claim the COGNEE-35 coupon in the Cognee Cloud console).

Usage:
    python scripts/seed_team_memory.py            # seed + recall smoke
    python scripts/seed_team_memory.py --reset     # forget() first, then seed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.cognee.factory import get as get_cognee  # noqa: E402
from shared.config import settings  # noqa: E402
from shared.models import MemoryItem  # noqa: E402

_HISTORY = (
    Path(__file__).resolve().parent.parent
    / "integrations"
    / "cognee"
    / "fixtures"
    / "team_history.json"
)
# What the reviewer would ask memory about when reviewing PR #43 (def5678), which
# repeats the same N+1 pattern in profile/views.py.
_SMOKE_QUERY = "N+1 query looping over records and querying inside the loop"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="forget() existing memory first")
    args = parser.parse_args()

    mem = get_cognee()
    print(f"memory backend: {mem.name} (mode={settings.memory_mode})")

    if args.reset:
        mem.forget()
        print("forgot existing memory")

    items = [MemoryItem(**d) for d in json.loads(_HISTORY.read_text(encoding="utf-8"))]
    for it in items:
        mem.remember(it)
    print(f"remembered {len(items)} item(s) from team_history.json")

    mem.improve()  # Cognee memify / re-index; no-op on the sim backend

    hits = mem.recall(_SMOKE_QUERY, limit=5)
    print(f"\nrecall smoke - query: {_SMOKE_QUERY!r}")
    if not hits:
        print("  (no hits) — check the backend and, in real mode, COGNEE_API_KEY")
        return 1
    for h in hits:
        print(f"  - [{h.severity.value}] {h.rule}: {h.comment[:90]}...")
    print("\nOK: remember -> recall works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
