"""Pytest configuration: ensure src/ is on sys.path and mock crewai."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src directory to Python path so tools can be imported
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Mock crewai entirely — tests import tools directly without a full crew run.
# We patch *before* any of our source modules are imported so that
# `from crewai.tools import tool` resolves to our no-op passthrough.
# ---------------------------------------------------------------------------

def _passthrough_tool(name_or_fn):
    """No-op decorator: registers a function as a tool but doesn't transform it."""
    if callable(name_or_fn):
        return name_or_fn  # used as @tool without arguments
    return lambda fn: fn  # used as @tool("ToolName")


# Build a mock crewai module tree
_mock_tools = MagicMock()
_mock_tools.tool = _passthrough_tool

_mock_crewai = MagicMock()
_mock_crewai.tools = _mock_tools
_mock_crewai.Crew = MagicMock
_mock_crewai.Process = MagicMock
_mock_crewai.Agent = MagicMock
_mock_crewai.Task = MagicMock
_mock_crewai.LLM = MagicMock

# Patch both the toplevel 'crewai' and 'crewai.tools' so
# `from crewai.tools import tool` works in the tools modules.
patcher_crewai = patch.dict(
    "sys.modules",
    {
        "crewai": _mock_crewai,
        "crewai.tools": _mock_tools,
        "crewai.tools.tool": _passthrough_tool,
    },
)
patcher_crewai.start()
