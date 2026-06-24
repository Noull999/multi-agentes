"""Tool: read code files from a directory."""

import os
import fnmatch
from pathlib import Path
from typing import Optional
from crewai.tools import tool

# Extensions que analizamos
TARGET_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs",
    ".py", ".rs", ".go", ".java", ".kt",
    ".vue", ".svelte",
    ".css", ".scss", ".json", ".yaml", ".yml",
    ".md", ".toml",
}

# Archivos/dirs a ignorar
IGNORE_PATTERNS = {
    "node_modules", ".git", ".next", ".vercel", "dist", "build",
    ".venv", "venv", "__pycache__", ".cache",
    "*.min.*", "*.bundle.*", "*.map",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".env", ".env.*",
}

MAX_FILE_SIZE = 100 * 1024  # 100KB
MAX_FILES = 50  # máx archivos por tanda


def _should_ignore(path: str, name: str) -> bool:
    rel = Path(path).relative_to(Path(path).anchor)
    parts = str(rel).split(os.sep) + [name]
    for pattern in IGNORE_PATTERNS:
        if any(fnmatch.fnmatch(p, pattern) for p in parts):
            return True
    return False


@tool("ReadSourceFiles")
def read_source_files(directory: str, pattern: Optional[str] = None) -> str:
    """
    Lee archivos de código fuente en un directorio.
    Recibe una ruta de directorio y opcionalmente un patrón glob (ej: "*.ts").
    Devuelve el contenido de cada archivo separado por marcadores.
    """
    base = Path(directory).expanduser().resolve()
    if not base.exists():
        return f"ERROR: El directorio '{directory}' no existe."

    if not base.is_dir():
        return f"ERROR: '{directory}' no es un directorio."

    # Recolectar archivos
    files = []
    for root, dirs, fnames in os.walk(base):
        # Podar directorios ignorados
        dirs[:] = [d for d in dirs if not _should_ignore(root, d)]

        for name in sorted(fnames):
            if _should_ignore(root, name):
                continue

            ext = Path(name).suffix
            if pattern and not fnmatch.fnmatch(name, pattern):
                continue
            if not pattern and ext not in TARGET_EXTENSIONS:
                continue

            fpath = Path(root) / name
            try:
                size = fpath.stat().st_size
                if size > MAX_FILE_SIZE:
                    continue
                files.append(fpath)
            except OSError:
                continue

    if not files:
        return f"No se encontraron archivos de código en '{directory}'."

    # Limitar cantidad
    files = files[:MAX_FILES]

    # Leer contenido
    result_parts = []
    for fpath in files:
        rel_path = fpath.relative_to(base)
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
            result_parts.append(f"## FILE: {rel_path}\n```\n{content}\n```")
        except Exception as e:
            result_parts.append(f"## FILE: {rel_path}\n*Error leyendo: {e}*")

    summary = f"📁 {len(files)} archivos leídos de {directory}"
    return f"{summary}\n\n" + "\n\n".join(result_parts)
