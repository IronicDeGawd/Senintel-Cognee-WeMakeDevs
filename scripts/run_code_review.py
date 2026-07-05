"""Run one Code Guardian cycle from the CLI and print the emitted Signal.

    python scripts/run_code_review.py abc1234
    python scripts/run_code_review.py 4093386568d25690acfe8364af9823cd42dde1f3

Sim path (SENTINEL_GL_MODE=sim): reviews the canned N+1 diff. One live Gemini
review call + one CI RCA call. Writes the comment to out/mr_note_<iid>.md.

Real path (SENTINEL_GL_MODE=real): resolves the MR for the commit via the GitLab
MCP server, reviews the live diff, posts the comment back on the MR. First MCP
call triggers OAuth in a browser; subsequent calls reuse ~/.mcp-auth/.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.sentinel.pillars.code_guardian.cycle import run_code_guardian_cycle  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python scripts/run_code_review.py <commit-sha>", file=sys.stderr)
        raise SystemExit(2)
    commit = sys.argv[1]
    signal = run_code_guardian_cycle(commit)
    print(signal.model_dump_json(indent=2))
    print(f"\nposted review -> {signal.detail['posted_to']}")


if __name__ == "__main__":
    main()
