"""Tests for IT Support Bot tools and utilities."""

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add src to path for imports
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# ── test_path_traversal_rejected ─────────────────────────────────────────

class TestPathTraversal:
    """generate_support_report must sanitize client_name to prevent path traversal."""

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        import tools.report_generator as rg

        orig = rg.REPORTS_DIR
        try:
            rg.REPORTS_DIR = tmp_path

            result = rg.generate_support_report(
                client_name="../../../etc/passwd",
                issue_description="Test issue",
                diagnosis="Test diagnosis",
                solution="Test solution",
                steps_performed="Step 1",
                recommendations="None",
            )

            assert "✅ Reporte guardado:" in result

            path_str = result.split("✅ Reporte guardado:")[1].strip()
            file_path = Path(path_str)

            # Path must stay inside tmp_path
            assert file_path.parent == tmp_path
            # No traversal chars in name
            assert ".." not in file_path.name
            assert "/" not in file_path.name
            # File must actually exist
            assert file_path.exists()
            # Should contain expected report content
            content = file_path.read_text(encoding="utf-8")
            assert "Reporte de Soporte" in content

        finally:
            rg.REPORTS_DIR = orig


# ── test_kb_search ───────────────────────────────────────────────────────

class TestKnowledgeBase:
    """search_knowledge_base returns correct results for known/unknown issues."""

    def test_kb_search_internet_no_connection(self) -> None:
        from tools.web_search import search_knowledge_base

        result = search_knowledge_base("internet", "no connection")
        assert "Base de Conocimiento" in result
        assert "ipconfig" in result
        assert "internet: no_connection" in result

    def test_kb_search_hardware_no_boot(self) -> None:
        from tools.web_search import search_knowledge_base

        result = search_knowledge_base("hardware", "no boot")
        assert "Base de Conocimiento" in result
        assert "fuent" in result or "POST" in result or "RAM" in result

    def test_kb_search_known_symptoms(self) -> None:
        from tools.web_search import search_knowledge_base

        result = search_knowledge_base("software", "blue screen")
        assert "Base de Conocimiento" in result
        assert "sfc /scannow" in result or "código de error" in result

    def test_kb_search_unknown_issue(self) -> None:
        from tools.web_search import search_knowledge_base

        result = search_knowledge_base("nonexistent_category", "weird symptom")
        assert "No encontré una entrada exacta" in result
        assert "Entradas disponibles" in result


# ── test_web_search_handles_error ────────────────────────────────────────

class TestWebSearchErrorHandling:
    """web_search must not crash when the network call fails."""

    def test_web_search_handles_network_error(self) -> None:
        from tools.web_search import web_search

        with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
            result = web_search("test query")
            assert "Error en búsqueda web" in result
            assert isinstance(result, str)

    def test_web_search_handles_timeout(self) -> None:
        from tools.web_search import web_search

        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            result = web_search("timeout test")
            assert "Error en búsqueda web" in result
            assert isinstance(result, str)

    def test_web_search_handles_json_decode_error(self) -> None:
        from tools.web_search import web_search

        mock_response = type("MockResponse", (), {"read": lambda self, **kw: b"not json"})()
        with patch("urllib.request.urlopen", return_value=mock_response):
            with patch("json.loads", side_effect=ValueError("Invalid JSON")):
                result = web_search("json error test")
                assert "Error en búsqueda web" in result
                assert isinstance(result, str)

    def test_web_search_successful_response(self) -> None:
        from tools.web_search import web_search

        mock_data = {
            "AbstractText": "How to fix a computer that won't turn on.",
            "AbstractURL": "https://example.com/fix-computer",
            "Heading": "Computer Fix Guide",
            "RelatedTopics": [],
        }

        class MockResponse:
            def read(self, **kw):  # type: ignore[no-untyped-def]
                return __import__("json").dumps(mock_data).encode()
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self
            def __exit__(self, *args):  # type: ignore[no-untyped-def]
                pass

        with patch("urllib.request.urlopen", return_value=MockResponse()):
            result = web_search("fix computer")
            assert "Resultados de búsqueda" in result
            assert "Computer Fix Guide" in result


# ── test_report_saved_in_reports_dir ─────────────────────────────────────

class TestReportSaved:
    """generate_support_report saves the report file in the reports directory."""

    def test_report_saved_in_reports_dir(self, tmp_path: Path) -> None:
        import tools.report_generator as rg

        orig = rg.REPORTS_DIR
        try:
            rg.REPORTS_DIR = tmp_path

            result = rg.generate_support_report(
                client_name="Test Client",
                issue_description="PC won't boot",
                diagnosis="Power supply failure",
                solution="Replaced PSU",
                steps_performed="1. Tested PSU\n2. Replaced unit",
                recommendations="Consider a UPS",
            )

            assert "✅ Reporte guardado:" in result
            path_str = result.split("✅ Reporte guardado:")[1].strip()
            file_path = Path(path_str)

            # Must live inside tmp_path
            assert file_path.parent == tmp_path
            assert file_path.exists()
            # Filename should reflect sanitized client name
            assert "test-client" in file_path.name
            # Content must be valid markdown with expected sections
            content = file_path.read_text(encoding="utf-8")
            assert "Reporte de Soporte Técnico" in content
            assert "Test Client" in content
            assert "Power supply failure" in content
            assert "Recomendaciones" in content

        finally:
            rg.REPORTS_DIR = orig


# ── test_env_parser_handles_quotes ───────────────────────────────────────

class TestEnvParser:
    """load_env must correctly parse quoted values, plain values, and comments."""

    _set_keys: set[str]

    def _write_env(self, content: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Write temp .env content and run load_env with patched Path."""
        from pathlib import Path as P

        self._set_keys = set()

        orig_read_text = P.read_text
        orig_exists = P.exists

        def mock_read_text(path_self: P, *args: Any, **kwargs: Any) -> str:
            if path_self.name == ".env":
                return content
            return orig_read_text(path_self, *args, **kwargs)

        def mock_exists(path_self: P) -> bool:
            if path_self.name == ".env":
                return True
            return orig_exists(path_self)

        monkeypatch.setattr(P, "read_text", mock_read_text)
        monkeypatch.setattr(P, "exists", mock_exists)

        from main import load_env

        before = set(os.environ.keys())
        load_env()
        after = set(os.environ.keys())
        self._set_keys = after - before

    def _cleanup(self) -> None:
        for k in self._set_keys:
            os.environ.pop(k, None)

    def test_env_parser_handles_quotes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Quoted values should strip the quotes and keep the inner value."""
        content = (
            'DB_HOST="localhost"\n'
            'DB_PORT=5432  # inline comment\n'
            'SECRET=my_secret\n'
            'EMPTY=\n'
        )
        self._write_env(content, monkeypatch)
        try:
            assert os.environ["DB_HOST"] == "localhost"
            assert os.environ["DB_PORT"] == "5432"
            assert os.environ["SECRET"] == "my_secret"
        finally:
            self._cleanup()

    def test_env_parser_handles_inline_comments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Inline comments after unquoted values should be stripped."""
        content = (
            'API_KEY=sk-abc123  # this is a comment\n'
            'MODE=production  # trailing comment\n'
        )
        self._write_env(content, monkeypatch)
        try:
            assert os.environ["API_KEY"] == "sk-abc123"
            assert os.environ["MODE"] == "production"
        finally:
            self._cleanup()

    def test_env_parser_handles_hashtag_in_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A quoted value containing # should keep the hash."""
        content = 'PASSWORD="my#pass!@#"\n'
        self._write_env(content, monkeypatch)
        try:
            assert os.environ["PASSWORD"] == "my#pass!@#"
        finally:
            self._cleanup()

    def test_env_parser_skips_comments_and_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lines that are comments or empty should be skipped."""
        content = (
            "# This is a comment\n"
            "EMPTY_LINE_AFTER=val\n"
            "\n"
            "# Another comment\n"
            "DEBUG=true\n"
        )
        self._write_env(content, monkeypatch)
        try:
            assert os.environ["EMPTY_LINE_AFTER"] == "val"
            assert os.environ["DEBUG"] == "true"
        finally:
            self._cleanup()
