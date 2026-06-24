"""Tests for code review tools."""

import os
import tempfile
from pathlib import Path

from tools.code_reader import _should_ignore, read_source_files
from tools.reporter import generate_review_report, list_files_in_repo


def test_path_traversal_rejected() -> None:
    """Verify list_files_in_repo rejects paths with ../ that escape allowed_base."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["CODE_REVIEW_TARGET"] = tmpdir
        try:
            result = list_files_in_repo(f"{tmpdir}/../etc")
            assert "ERROR" in result or "está fuera" in result
        finally:
            os.environ.pop("CODE_REVIEW_TARGET", None)


def test_path_traversal_code_reader() -> None:
    """Verify read_source_files skips symlinks that point outside the base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "base"
        base.mkdir()
        outside = Path(tmpdir) / "outside"
        outside.mkdir()
        secret = outside / "secret.py"
        secret.write_text("SECRET = 1")

        # Symlink inside base that points outside
        link = base / "leak.py"
        link.symlink_to(secret)

        result = read_source_files(str(base))
        assert "leak" not in result
        assert "SECRET" not in result


def test_symlink_skipped() -> None:
    """Verify symlinks are skipped by code_reader."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        real_file = base / "real.py"
        real_file.write_text("x = 1")
        link = base / "link.py"
        link.symlink_to(real_file)

        result = read_source_files(str(base))
        assert "link.py" not in result
        assert "real.py" in result


def test_report_saved_in_reports_dir() -> None:
    """Verify generate_review_report saves files inside reports/ directory."""
    result = generate_review_report("# Test Report Content")
    assert "Reporte guardado" in result
    # Extract the path and verify it's inside a reports directory
    path_str = result.split(": ")[-1].strip()
    report_path = Path(path_str)
    assert report_path.exists()
    assert "reports" in str(report_path)


def test_generate_review_report_output() -> None:
    """Basic test of generate_review_report output format and content."""
    result = generate_review_report("## Bugs Found\nNone.")
    assert "Reporte guardado" in result
    assert result.startswith("✅") or "Reporte guardado" in result
    # Verify the report file contains the expected header
    path_str = result.split(": ")[-1].strip()
    report_content = Path(path_str).read_text(encoding="utf-8")
    assert "# 🔍 Code Review Report" in report_content
    assert "## Bugs Found" in report_content


def test_should_ignore_filters() -> None:
    """Verify _should_ignore correctly filters paths based on IGNORE_PATTERNS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Files/paths that should be ignored
        assert _should_ignore(base, str(base / "node_modules"), "somefile.js") is True
        assert _should_ignore(base, str(base), ".git") is True
        assert _should_ignore(base, str(base / "subdir"), "__pycache__") is True
        assert _should_ignore(base, str(base), ".venv") is True
        assert _should_ignore(base, str(base / "dist"), "bundle.js") is True

        # Normal files should NOT be ignored
        assert _should_ignore(base, str(base), "main.py") is False
        assert _should_ignore(base, str(base / "src"), "app.ts") is False

        # Files outside the base directory should be ignored
        assert _should_ignore(base, "/etc", "passwd") is True
