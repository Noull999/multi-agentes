"""
Multi-Agentes API — FastAPI backend
Expone los 3 agentes como endpoints REST con auth y job queue async.
"""

import asyncio
import os
import shlex
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

# ─── App setup ─────────────────────────────────────────────────

app = FastAPI(
    title="Multi-Agentes API",
    description="Code Review · IT Support · Consultor Full-Stack",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = Path("/app")
VENV = "source .venv/bin/activate"

# ─── Auth ──────────────────────────────────────────────────────

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_CONFIGURED_KEY: Optional[str] = os.getenv("API_KEY", "").strip() or None

if not _CONFIGURED_KEY:
    import logging
    logging.getLogger("uvicorn.error").warning(
        "API_KEY no configurada — todos los endpoints son públicos. "
        "Agrega API_KEY=<clave> en .env para protegerlos."
    )


async def require_auth(key: Optional[str] = Security(_API_KEY_HEADER)) -> None:
    """Dependencia de autenticación. No-op si API_KEY no está configurada."""
    if _CONFIGURED_KEY and key != _CONFIGURED_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key inválida o ausente",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# ─── Job store (in-memory) ─────────────────────────────────────

_jobs: dict[str, dict] = {}  # job_id → job data

MAX_JOBS = 200  # evitar crecimiento ilimitado en memoria


def _new_job(agent: str) -> dict:
    job_id = uuid.uuid4().hex[:10]
    job = {
        "job_id": job_id,
        "agent": agent,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "result": None,
    }
    if len(_jobs) >= MAX_JOBS:
        # Eliminar el job más antiguo
        oldest = next(iter(_jobs))
        del _jobs[oldest]
    _jobs[job_id] = job
    return job


# ─── Request models ────────────────────────────────────────────

class ReviewRequest(BaseModel):
    path: str = Field(..., description="Ruta del proyecto a revisar")
    model: str = Field("kimi-k2.7-code", description="Modelo LLM a usar")

class SupportRequest(BaseModel):
    issue: str = Field(..., description="Descripción del problema IT")
    client: str = Field("Cliente", description="Nombre del cliente")
    model: str = Field("deepseek-v4-flash", description="Modelo LLM a usar")

class ConsultorRequest(BaseModel):
    description: str = Field(..., description="Descripción del proyecto/cliente")
    model: str = Field("kimi-k2.7-code", description="Modelo LLM a usar")


# ─── Runner (blocking — se ejecuta en threadpool) ──────────────

def _run_agent_sync(proj: str, cmd: list, timeout: int = 600) -> dict:
    safe_cmd = " ".join(shlex.quote(str(arg)) for arg in cmd)
    full_cmd = f"cd {BASE}/{proj} && {VENV} && {safe_cmd}"
    try:
        result = subprocess.run(
            ["bash", "-c", full_cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-50_000:],
            "stderr": result.stderr[-10_000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout (máx 10 min)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _dispatch(job_id: str, proj: str, cmd: list) -> None:
    """Ejecuta el agente en un hilo y actualiza el job cuando termina."""
    _jobs[job_id]["status"] = "running"
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_agent_sync, proj, cmd)
    _jobs[job_id].update(
        status="done" if result.get("success") else "error",
        result=result,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )


# ─── Endpoints públicos ────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    auth_badge = (
        '<span style="color:#4ade80">🔒 Auth activa</span>'
        if _CONFIGURED_KEY else
        '<span style="color:#facc15">⚠️ Sin auth</span>'
    )
    return f"""<!DOCTYPE html>
<html>
<head><title>Multi-Agentes API</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}}
  .card{{background:#1e293b;border-radius:16px;padding:40px;max-width:520px;width:90%;box-shadow:0 25px 50px rgba(0,0,0,.5);text-align:center}}
  h1{{font-size:2rem;margin-bottom:8px}} p{{color:#94a3b8;margin-bottom:24px}}
  .ep{{text-align:left;background:#0f172a;border-radius:8px;padding:16px;margin-bottom:16px}}
  .ep code{{display:block;padding:4px 0;color:#38bdf8;font-size:.85rem}}
  .badge{{display:inline-block;background:#3b82f6;color:#fff;padding:4px 12px;border-radius:20px;font-size:.8rem;margin:4px}}
  a{{color:#38bdf8}}
</style>
</head>
<body>
<div class="card">
  <h1>Multi-Agentes</h1>
  <p>API v1.1 — {auth_badge}</p>
  <div class="ep">
    <code>POST /api/code-review  — revisar código fuente</code>
    <code>POST /api/it-support   — diagnosticar problema IT</code>
    <code>POST /api/consultor    — generar propuesta + código</code>
    <code>GET  /api/job/{{id}}     — estado de un job</code>
    <code>GET  /api/jobs          — últimos jobs</code>
  </div>
  <a class="badge" href="/docs">Documentación</a>
  <a class="badge" href="/api/jobs">Jobs recientes</a>
</div>
</body>
</html>"""


@app.get("/health", tags=["sistema"])
async def health():
    return {
        "status": "ok",
        "agents": ["code-review", "it-support", "consultor"],
        "auth": bool(_CONFIGURED_KEY),
        "jobs_en_memoria": len(_jobs),
    }


# ─── Job endpoints ─────────────────────────────────────────────

@app.get("/api/jobs", tags=["jobs"])
async def list_jobs(_: None = Security(require_auth)):
    """Devuelve los últimos MAX_JOBS jobs (sin resultado completo para no saturar)."""
    summary = []
    for job in reversed(list(_jobs.values())):
        summary.append({
            "job_id": job["job_id"],
            "agent": job["agent"],
            "status": job["status"],
            "created_at": job["created_at"],
            "finished_at": job["finished_at"],
        })
    return {"total": len(summary), "jobs": summary[:50]}


@app.get("/api/job/{job_id}", tags=["jobs"])
async def get_job(job_id: str, _: None = Security(require_auth)):
    """Devuelve el estado y resultado de un job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' no encontrado")
    return job


# ─── Agent endpoints ───────────────────────────────────────────

@app.post("/api/code-review", status_code=202, tags=["agentes"])
async def code_review(req: ReviewRequest, _: None = Security(require_auth)):
    """
    Lanza un Code Review multi-agente en background.
    Devuelve un job_id para consultar el resultado con GET /api/job/{job_id}.
    """
    if not Path(req.path).exists():
        raise HTTPException(400, f"Ruta '{req.path}' no existe en el servidor")

    job = _new_job("code-review")
    asyncio.create_task(_dispatch(job["job_id"], "code-review-bot", [
        "python", "src/main.py", req.path,
        "--opencode", "--model", req.model,
    ]))
    return {"job_id": job["job_id"], "status": "queued", "poll": f"/api/job/{job['job_id']}"}


@app.post("/api/it-support", status_code=202, tags=["agentes"])
async def it_support(req: SupportRequest, _: None = Security(require_auth)):
    """
    Lanza un diagnóstico IT multi-agente en background.
    Devuelve un job_id para consultar el resultado con GET /api/job/{job_id}.
    """
    job = _new_job("it-support")
    asyncio.create_task(_dispatch(job["job_id"], "it-support-bot", [
        "python", "src/main.py", req.issue,
        "--opencode", "--model", req.model,
        "--client", req.client,
    ]))
    return {"job_id": job["job_id"], "status": "queued", "poll": f"/api/job/{job['job_id']}"}


@app.post("/api/consultor", status_code=202, tags=["agentes"])
async def consultor(req: ConsultorRequest, _: None = Security(require_auth)):
    """
    Lanza el Consultor Full-Stack en background.
    Devuelve un job_id para consultar el resultado con GET /api/job/{job_id}.
    """
    job = _new_job("consultor")
    asyncio.create_task(_dispatch(job["job_id"], "consultor-bot", [
        "python", "src/main.py", "--input", req.description,
        "--opencode", "--model", req.model,
    ]))
    return {"job_id": job["job_id"], "status": "queued", "poll": f"/api/job/{job['job_id']}"}
