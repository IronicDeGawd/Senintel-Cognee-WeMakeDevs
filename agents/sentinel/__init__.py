"""Sentinel root orchestrator package. `adk run agents.sentinel` imports
root_agent from agent.py."""

from agents.sentinel.agent import root_agent

__all__ = ["root_agent"]
