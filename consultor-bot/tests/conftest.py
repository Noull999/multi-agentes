"""Pytest configuration — mock crewai so @tool does not wrap functions in Tool objects.

Without this mock, the real ``crewai.tools.tool`` decorator wraps each function in a
``Tool`` instance that is *not* directly callable, causing every test that invokes
``scaffold_project(…)`` / ``generate_code_file(…)`` etc. to fail with::

    TypeError: 'Tool' object is not callable

The mock returns the original function unchanged so tests can exercise the logic
directly.  It also provides a lightweight ``ToolException`` so that the
``generate_code_file`` error path can still raise and be caught.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# 1.  Ensure the ``src`` package is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # consultor-bot/
_SRC = str(_PROJECT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# ---------------------------------------------------------------------------
# 2.  Mock crewai *before* any test module triggers a real import
# ---------------------------------------------------------------------------


class _MockToolException(Exception):
    """Stand-in for ``crewai.tools.ToolException``."""


def _mock_tool(name=None):
    """Replacement for ``@tool`` — returns the decorated function unchanged.

    Handles both usage patterns::

        @tool("Name")
        def fn(...): ...

    and (future) ::

        @tool
        def fn(...): ...
    """

    def decorator(func):
        return func

    if callable(name):  # @tool (no call)
        return name
    return decorator  # @tool("Name")


# Build the mock module hierarchy
_tools_module = MagicMock()
_tools_module.tool = _mock_tool
_tools_module.ToolException = _MockToolException

_crewai_module = MagicMock()
_crewai_module.tools = _tools_module
_crewai_module.Agent = MagicMock
_crewai_module.Crew = MagicMock
_crewai_module.Process = MagicMock
_crewai_module.Task = MagicMock
_crewai_module.LLM = MagicMock

# Install into sys.modules before any real imports can happen.
# The ``@tool`` decorator is evaluated at ``import`` time, so the mock must
# already be present when ``tools.project_tools`` is first loaded.
sys.modules["crewai"] = _crewai_module
sys.modules["crewai.tools"] = _tools_module
