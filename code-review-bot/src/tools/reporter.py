"""Tool: generate structured reports."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from crewai.tools import tool

# Output directory for reports — sandboxed against project root
_CODE_REVIEW_ROOT: Path = Path(__file__).resolve().parent.parent.parent  # project root
_REPORTS_ENV: Optional[str] = os.getenv("CODE_REVIEW_OUTPUT", "./reports")
REPORTS_DIR: Path = Path(_REPORTS_ENV).resolve()
# P0: constrain to project root — reject env var paths that escape
try:
    REPORTS_DIR.relative_to(_CODE_REVIEW_ROOT)
except ValueError:
    REPORTS_DIR = _CODE_REVIEW_ROOT / "reports"
    print(f"⚠️ CODE_REVIEW_OUTPUT='{_REPORTS_ENV}' escapa del proyecto. Usando: {REPORTS_DIR}")


@tool("GenerateReviewReport")
def generate_review_report(report_content: str) -> str:
    """
    Genera un reporte de revisión de código en formato markdown.
    Recibe el contenido del reporte.
    Devuelve la ruta donde se guardó (siempre dentro de reports/).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = f"code-review-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    header = f"""# 🔍 Code Review Report
**Generado:** {timestamp}

---

"""

    # P0: escape only < > to prevent HTML injection without corrupting markdown
    safe_content = report_content.replace("<", "&lt;").replace(">", "&gt;")
    full = header + safe_content
    out_path = REPORTS_DIR / filename

    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full, encoding="utf-8")
        return f"✅ Reporte guardado en: {out_path}"
    except Exception as e:
        return f"⚠️ No se pudo guardar: {e}"


@tool("ListFilesInRepo")
def list_files_in_repo(directory: str, extension: str = "") -> str:
    """
    Lista los archivos en un directorio, opcionalmente filtrados por extensión.
    Ejemplo: extension=".ts" para solo TypeScript.
    """
    import os
    from pathlib import Path

    base = Path(directory).expanduser().resolve()
    # P0: bind to validated directory — reject path traversal
    allowed_base = Path(os.getenv("CODE_REVIEW_TARGET", ".")).resolve()
    try:
        base.relative_to(allowed_base)
    except ValueError:
        return f"ERROR: '{directory}' está fuera del directorio permitido ({allowed_base})"

    if not base.exists():
        return f"ERROR: '{directory}' no existe"

    result = []
    for root, dirs, fnames in os.walk(base):
        # saltar carpetas comunes
        dirs[:] = [d for d in dirs if not d.startswith((".", "node_modules", "venv"))]
        for name in sorted(fnames):
            if extension and not name.endswith(extension):
                continue
            rel = Path(root).relative_to(base)
            result.append(str(rel / name))

    if not result:
        return f"No hay archivos{' con extensión ' + extension if extension else ''} en {directory}"

    return f"📁 {len(result)} archivos:\n" + "\n".join(result[:200])
