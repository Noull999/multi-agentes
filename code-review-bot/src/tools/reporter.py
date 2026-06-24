"""Tool: generate structured reports."""

from datetime import datetime
from crewai.tools import tool


@tool("GenerateReviewReport")
def generate_review_report(report_content: str, output_path: str = "") -> str:
    """
    Genera un reporte de revisión de código en formato markdown.
    Recibe el contenido del reporte y opcionalmente una ruta de salida.
    Devuelve la ruta donde se guardó.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = f"""# 🔍 Code Review Report
**Generado:** {timestamp}

---

"""

    full = header + report_content

    if not output_path:
        output_path = f"code-review-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full)
        return f"✅ Reporte guardado en: {output_path}"
    except Exception as e:
        # fallback: devolver el contenido
        return f"⚠️ No se pudo guardar: {e}\n\n---\n{full}"


@tool("ListFilesInRepo")
def list_files_in_repo(directory: str, extension: str = "") -> str:
    """
    Lista los archivos en un directorio, opcionalmente filtrados por extensión.
    Ejemplo: extension=".ts" para solo TypeScript.
    """
    import os
    from pathlib import Path

    base = Path(directory).expanduser().resolve()
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
