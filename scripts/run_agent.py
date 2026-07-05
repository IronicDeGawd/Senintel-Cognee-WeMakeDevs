"""Local harness — run one turn against the root agent and print output.
Carries the spike's InMemoryRunner pattern (no `adk run` needed).

Usage:
    python scripts/run_agent.py "say hi in one sentence"
"""

from __future__ import annotations

import asyncio
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from agents.sentinel.agent import root_agent  # noqa: E402
from shared.observability import init_tracing  # noqa: E402


async def run_turn(user_text: str) -> None:
    app_name, user_id, session_id = "sentinel", "local_user", secrets.token_hex(8)
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)
    await runner.session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=user_text)]),
    ):
        for part in (event.content.parts if event.content else []) or []:
            if getattr(part, "function_call", None):
                print(f"\n[tool call] {part.function_call.name}")
            elif getattr(part, "text", None):
                print(part.text, end="")
    print()


def main() -> None:
    init_tracing()  # no-op unless DT_OTLP_ENDPOINT + DT_API_TOKEN are set
    msg = sys.argv[1] if len(sys.argv) > 1 else "say hi in one sentence"
    asyncio.run(run_turn(msg))


if __name__ == "__main__":
    main()
