"""pytest configuration: mock crewai early to prevent slow/hanging imports."""

import sys
import types
from unittest.mock import MagicMock

# ── Build a mock crewai module tree ──────────────────────────────────────

def _build_mock_crewai() -> types.ModuleType:
    """Create a mock crewai module so imports don't trigger real loading."""
    crewai = types.ModuleType("crewai")
    crewai.__path__ = []  # make it a package
    crewai.__file__ = "<mock>"

    # Agent
    agent_cls = MagicMock(name="Agent")
    crewai.Agent = agent_cls

    # Task
    task_cls = MagicMock(name="Task")
    crewai.Task = task_cls

    # Crew
    crew_cls = MagicMock(name="Crew")
    crewai.Crew = crew_cls

    # Process
    class FakeProcess:
        sequential = "sequential"
    crewai.Process = FakeProcess()

    # LLM
    llm_cls = MagicMock(name="LLM")
    crewai.LLM = llm_cls

    # tools sub-module
    tools_mod = types.ModuleType("crewai.tools")
    tools_mod.__file__ = "<mock>"
    tools_mod.__path__ = []

    # @tool decorator — identity decorator that returns the function as-is
    def tool_decorator(name: str = "") -> callable:
        def wrapper(fn: callable) -> callable:
            fn._tool_name = name
            return fn
        return wrapper

    tools_mod.tool = tool_decorator
    crewai.tools = tools_mod

    return crewai


# Inject into sys.modules BEFORE any test imports happen
_mock_crewai = _build_mock_crewai()
sys.modules["crewai"] = _mock_crewai
sys.modules["crewai.tools"] = _mock_crewai.tools
sys.modules["crewai.Agent"] = _mock_crewai.Agent  # type: ignore[attr-defined]
sys.modules["crewai.Task"] = _mock_crewai.Task  # type: ignore[attr-defined]
sys.modules["crewai.Crew"] = _mock_crewai.Crew  # type: ignore[attr-defined]
sys.modules["crewai.LLM"] = _mock_crewai.LLM  # type: ignore[attr-defined]
sys.modules["crewai.Process"] = _mock_crewai.Process  # type: ignore[attr-defined]
