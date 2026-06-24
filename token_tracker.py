"""
Token Usage Tracker — registra y consulta uso de tokens por modelo.

Uso desde cualquier proyecto:
  from token_tracker import log_usage, get_stats, format_stats, patch_litellm

  # Al inicio del proyecto, parchar litellm para tracking automático:
  patch_litellm(project_name="code-review-bot")

  # O manualmente después de cada llamada:
  log_usage("gpt-4o", prompt_tokens=100, completion_tokens=50, project="my-project")

  # Para ver estadísticas:
  print(format_stats())
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

TRACKER_FILE = Path.home() / ".hermes" / "token_usage.json"


def _load() -> dict:
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text())
    return {"calls": [], "models": {}}


def _save(data: dict) -> None:
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def log_usage(
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    project: str = "unknown",
) -> None:
    """Registra una llamada a LLM con su uso de tokens."""
    data = _load()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "project": project,
    }
    data["calls"].append(entry)

    # Acumular por modelo
    mod = data["models"].setdefault(
        model, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    mod["calls"] += 1
    mod["prompt_tokens"] += prompt_tokens
    mod["completion_tokens"] += completion_tokens
    mod["total_tokens"] += total_tokens

    _save(data)


def get_stats() -> dict:
    """Retorna dict con estadísticas por modelo."""
    return _load()["models"]


def get_recent_calls(limit: int = 5) -> list:
    """Retorna las últimas N llamadas."""
    data = _load()
    return data["calls"][-limit:]


def format_stats() -> str:
    """Formatea estadísticas como texto legible."""
    stats = get_stats()
    if not stats:
        return "📊 *Token Usage*\n\nNo hay registros aún. Los tokens se empiezan a contar desde que instalas el tracker."

    lines = ["📊 **Token Usage por Modelo**\n"]
    total_all = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for model, info in sorted(stats.items()):
        lines.append(f"▸ *{model}*")
        lines.append(f"  Llamadas: {info['calls']}")
        lines.append(f"  Prompt: {info['prompt_tokens']:,} tokens")
        lines.append(f"  Completion: {info['completion_tokens']:,} tokens")
        lines.append(f"  Total: {info['total_tokens']:,} tokens")
        lines.append("")
        for k in total_all:
            total_all[k] += info[k]

    lines.append(f"**TOTAL GENERAL**")
    lines.append(f"  Llamadas: {total_all['calls']}")
    lines.append(f"  Prompt: {total_all['prompt_tokens']:,} tokens")
    lines.append(f"  Completion: {total_all['completion_tokens']:,} tokens")
    lines.append(f"  Total: {total_all['total_tokens']:,} tokens")

    return "\n".join(lines)


def patch_litellm(project_name: str = "unknown") -> None:
    """
    Parchea litellm.completion para trackear tokens automáticamente.
    Llama esto UNA VEZ al inicio del proyecto (después de importar litellm).
    """
    try:
        import litellm
        original_completion = litellm.completion

        def tracked_completion(*args, **kwargs):
            resp = original_completion(*args, **kwargs)
            try:
                model = kwargs.get("model", resp.model if hasattr(resp, "model") else "unknown")
                usage = getattr(resp, "usage", None)
                if usage:
                    log_usage(
                        model=model,
                        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                        total_tokens=getattr(usage, "total_tokens", 0) or 0,
                        project=project_name,
                    )
            except Exception:
                pass  # Si falla el tracking, no afecta la respuesta
            return resp

        litellm.completion = tracked_completion
        print(f"  📊 Token tracker activo para: {project_name}")
    except ImportError:
        print("  ⚠️ litellm no disponible — token tracker desactivado")
