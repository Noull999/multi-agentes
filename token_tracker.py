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

# Límite por sesión de OpenCode Go: 1M tokens cada 5h
SESSION_LIMIT = 1_000_000
SESSION_WINDOW_HOURS = 5


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


def get_session_usage() -> dict:
    """Retorna uso de tokens en la ventana actual de 5h."""
    from datetime import timedelta
    data = _load()
    now = datetime.now()
    window_start = now - timedelta(hours=SESSION_WINDOW_HOURS)

    session_total = 0
    session_prompt = 0
    session_completion = 0
    session_count = 0

    for c in data["calls"]:
        try:
            ts = c["timestamp"]
            if isinstance(ts, str):
                # Strip timezone info if present
                ts = ts.replace("Z", "")
                if "+" in ts or ts.endswith("+00:00"):
                    ts = ts.split("+")[0]
                c_time = datetime.fromisoformat(ts)
            else:
                continue
            if c_time >= window_start:
                session_total += c.get("total_tokens", 0)
                session_prompt += c.get("prompt_tokens", 0)
                session_completion += c.get("completion_tokens", 0)
                session_count += 1
        except (ValueError, TypeError):
            continue

    # Calcular tiempo hasta recarga desde la última llamada
    last_call_ts = window_start
    if data["calls"]:
        for c in reversed(data["calls"]):
            try:
                ts = c["timestamp"]
                if isinstance(ts, str):
                    ts = ts.replace("Z", "")
                    if "+" in ts or ts.endswith("+00:00"):
                        ts = ts.split("+")[0]
                    c_time = datetime.fromisoformat(ts)
                    last_call_ts = c_time
                    break
            except (ValueError, TypeError):
                continue

    next_reset = last_call_ts + timedelta(hours=SESSION_WINDOW_HOURS)
    remaining_secs = max(0, (next_reset - now).total_seconds())
    remaining_hours = round(remaining_secs / 3600, 1)

    return {
        "calls": session_count,
        "prompt_tokens": session_prompt,
        "completion_tokens": session_completion,
        "total_tokens": session_total,
        "limit": SESSION_LIMIT,
        "remaining_tokens": max(0, SESSION_LIMIT - session_total),
        "remaining_hours": remaining_hours,
        "next_reset": next_reset.isoformat(),
    }


def format_stats() -> str:
    """Formatea estadísticas como texto legible."""
    stats = get_stats()
    session = get_session_usage()
    if not stats:
        return "📊 *Token Usage*\n\nNo hay registros aún. Los tokens se empiezan a contar desde que instalas el tracker."

    lines = ["📊 **Token Usage — Sesión OpenCode Go**\n"]

    # Barra de progreso de sesión
    pct = (session["total_tokens"] / session["limit"]) * 100 if session["limit"] > 0 else 0
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    lines.append(f"**Sesión 5h ({SESSION_WINDOW_HOURS}h — límite {SESSION_LIMIT:,} tokens)**")
    lines.append(f"  {bar}  {pct:.1f}%")
    lines.append(f"  Usado: {session['total_tokens']:,} / {session['limit']:,} tokens")
    lines.append(f"  Restante: {session['remaining_tokens']:,} tokens")
    lines.append(f"  Recarga: ~{session['remaining_hours']}h")
    lines.append(f"  Llamadas en sesión: {session['calls']}")
    lines.append("")

    # Per-model breakdown
    lines.append("**Por modelo (histórico total)**")
    total_all = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for model, info in sorted(stats.items()):
        short_model = model.replace("openai/", "")
        lines.append(f"▸ *{short_model}*")
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
