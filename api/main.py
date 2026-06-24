"""
🤖 Multi-Agentes API — FastAPI backend
Expone los 3 agentes como endpoints REST
"""

import os
import subprocess
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="🤖 Multi-Agentes API",
    description="Code Review · IT Support · Consultor Full-Stack",
    version="1.0.0",
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


# ─── Models ───────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    path: str = Field(..., description="Ruta del proyecto a revisar")
    model: str = "kimi-k2.7-code"

class SupportRequest(BaseModel):
    issue: str = Field(..., description="Descripción del problema IT")
    client: str = "Cliente"
    model: str = "deepseek-v4-flash"

class ConsultorRequest(BaseModel):
    description: str = Field(..., description="Descripción del proyecto/cliente")
    model: str = "kimi-k2.7-code"


# ─── Runner helper ─────────────────────────────────────────────

def run_agent(proj: str, cmd: list, timeout: int = 600):
    """Run an agent and return its output."""
    full_cmd = f"cd {BASE}/{proj} && {VENV} && " + " ".join(cmd)
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
            "stdout": result.stdout[-50000:],  # last 50k chars
            "stderr": result.stderr[-10000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout (max 10 min)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Endpoints ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
    <head><title>🤖 Multi-Agentes</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .card { background: #1e293b; border-radius: 16px; padding: 40px; max-width: 480px; width: 90%; box-shadow: 0 25px 50px rgba(0,0,0,0.5); text-align: center; }
        h1 { font-size: 2rem; margin-bottom: 8px; }
        p { color: #94a3b8; margin-bottom: 24px; }
        .endpoints { text-align: left; background: #0f172a; border-radius: 8px; padding: 16px; }
        .endpoints code { display: block; padding: 4px 0; color: #38bdf8; font-size: 0.9rem; }
        .badge { display: inline-block; background: #3b82f6; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-top: 24px; }
        a { color: #38bdf8; }
    </style>
    </head>
    <body>
    <div class="card">
        <h1>🤖 Multi-Agentes</h1>
        <p>API lista — 3 endpoints disponibles</p>
        <div class="endpoints">
            <code>POST /api/code-review  ← ruta del proyecto</code>
            <code>POST /api/it-support   ← describe el problema</code>
            <code>POST /api/consultor    ← describe el proyecto</code>
        </div>
        <div class="badge"><a href="/docs">📋 Documentación API</a></div>
    </div>
    </body>
    </html>
    """


@app.post("/api/code-review")
async def code_review(req: ReviewRequest):
    if not Path(req.path).exists():
        raise HTTPException(400, f"Ruta '{req.path}' no existe")
    return run_agent("code-review-bot", [
        "python", "src/main.py", req.path,
        "--opencode", "--model", req.model,
    ])


@app.post("/api/it-support")
async def it_support(req: SupportRequest):
    return run_agent("it-support-bot", [
        "python", "src/main.py", req.issue,
        "--opencode", "--model", req.model,
        "--client", req.client,
    ])


@app.post("/api/consultor")
async def consultor(req: ConsultorRequest):
    return run_agent("consultor-bot", [
        "python", "src/main.py", "--input", req.description,
        "--opencode", "--model", req.model,
    ])


@app.get("/health")
async def health():
    return {"status": "ok", "agents": ["code-review", "it-support", "consultor"]}
