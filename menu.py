#!/usr/bin/env python3
"""
🤖 Multi-Agentes — Menú interactivo
Uso: python3 menu.py
"""

import subprocess
import sys
import os
from pathlib import Path

BASE = "/root/multi-agentes"
VENV_ACTIVATE = 'source .venv/bin/activate'

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    clear()
    print("╔══════════════════════════════════════════╗")
    print("║     🤖  MULTI-AGENTES - MENÚ            ║")
    print("╠══════════════════════════════════════════╣")
    print("║  OpenCode Go · CrewAI · 3 herramientas   ║")
    print("╚══════════════════════════════════════════╝")
    print()

def run_agent(proj: str, cmd: list, desc: str):
    print_header()
    print(f"▶  {desc}")
    print(f"   Proyecto: {proj}")
    print(f"   Comando: {' '.join(cmd[-3:])}")
    print(f"\n{'='*50}")
    
    full_cmd = f"cd {BASE}/{proj} && {VENV_ACTIVATE} && " + " ".join(cmd)
    
    try:
        result = subprocess.run(
            ["bash", "-c", full_cmd],
            timeout=600,
            capture_output=False,
            text=True
        )
        print(f"\n{'='*50}")
        if result.returncode == 124:
            input("\n⏱️  Tiempo agotado (10 min). Enter para continuar...")
        else:
            input(f"\n✅ Completado (exit: {result.returncode}). Enter para continuar...")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario.")
        input("Enter para continuar...")

def code_review():
    print_header()
    ruta = input("📁 Ruta del proyecto a revisar (ej: /root/projects/predial-lechero): ").strip()
    if not ruta:
        input("❌ Ruta vacía. Enter...")
        return
    if not Path(ruta).expanduser().exists():
        input(f"❌ La ruta '{ruta}' no existe. Enter...")
        return
    
    print("\n🧠 Modelos disponibles:")
    print(" 1) kimi-k2.7-code (⭐ especializado código)")
    print(" 2) deepseek-v4-pro (⭐ razonamiento profundo)")
    print(" 3) qwen3.7-plus (rápido)")
    print(" 4) deepseek-v4-flash (contexto largo)")
    m = input("Modelo (1-4) [default 1]: ").strip()
    modelos = ["kimi-k2.7-code", "deepseek-v4-pro", "qwen3.7-plus", "deepseek-v4-flash"]
    modelo = modelos[int(m)-1] if m in "1234" else modelos[0]
    
    run_agent("code-review-bot", [
        "python", "src/main.py", ruta, "--opencode", "--model", modelo
    ], f"🔍 Code Review: {Path(ruta).name}")

def it_support():
    print_header()
    problema = input("💻 Describe el problema IT: ").strip()
    if not problema:
        input("❌ Problema vacío. Enter...")
        return
    
    cliente = input("👤 Nombre del cliente [opcional]: ").strip()
    
    print("\n🧠 Modelos disponibles:")
    print(" 1) deepseek-v4-flash (⭐ recomendado, contexto largo)")
    print(" 2) qwen3.7-plus (rápido)")
    print(" 3) glm-5 (propósito general)")
    m = input("Modelo (1-3) [default 1]: ").strip()
    modelos = ["deepseek-v4-flash", "qwen3.7-plus", "glm-5"]
    modelo = modelos[int(m)-1] if m in "123" else modelos[0]
    
    cmd = ["python", "src/main.py", problema, "--opencode", "--model", modelo]
    if cliente:
        cmd += ["--client", cliente]
    
    run_agent("it-support-bot", cmd, f"🛠️  IT Support: {problema[:50]}")

def consultor():
    print_header()
    print("📝 Ingresa la descripción del proyecto/cliente:")
    print("  (Escribe 'EOF' en línea sola para terminar)")
    print()
    
    lines = []
    while True:
        line = input()
        if line.strip() == "EOF":
            break
        lines.append(line)
    
    descripcion = "\n".join(lines).strip()
    if not descripcion:
        input("❌ Descripción vacía. Enter...")
        return
    
    print("\n🧠 Modelos disponibles:")
    print(" 1) kimi-k2.7-code (⭐ especializado código + arquitectura)")
    print(" 2) deepseek-v4-pro (razonamiento profundo)")
    print(" 3) qwen3.7-plus (rápido, confiable)")
    m = input("Modelo (1-3) [default 1]: ").strip()
    modelos = ["kimi-k2.7-code", "deepseek-v4-pro", "qwen3.7-plus"]
    modelo = modelos[int(m)-1] if m in "123" else modelos[0]
    
    run_agent("consultor-bot", [
        "python", "src/main.py", "--input", descripcion, "--opencode", "--model", modelo
    ], f"🎯 Consultor: {descripcion[:50]}...")

def update_envs():
    """Update all .env files with recommended models"""
    models = {
        "code-review-bot": "kimi-k2.7-code",
        "it-support-bot": "deepseek-v4-flash",
        "consultor-bot": "kimi-k2.7-code",
    }
    
    for proj, model in models.items():
        env_path = Path(f"{BASE}/{proj}/.env")
        if not env_path.exists():
            continue
        txt = env_path.read_text()
        for ln in txt.splitlines():
            if ln.startswith("OPENCODE_API_KEY"):
                key = ln.split("=", 1)[1]
                break
        
        env_content = "\n".join([
            "# OpenCode Go API",
            "OPENCODE_API_KEY=" + key,
            f"OPENCODE_MODEL={model}",
            "OPENCODE_BASE_URL=https://opencode.ai/zen/go/v1",
            "",
            "OPENAI_API_KEY=" + key,
            ""
        ])
        env_path.write_text(env_content)
        print(f"  ✅ {proj}: {model}")

def about():
    print_header()
    print("🤖  MULTI-AGENTES v1.0")
    print()
    print("Stack: CrewAI 1.14 + OpenCode Go + Python 3.12")
    print()
    print("🔍 Code Review Bot  — 4 agentes")
    print("   Analiza código, busca bugs, revisa estilo, genera reporte")
    print()
    print("🛠️  IT Support Bot  — 4 agentes")
    print("   Diagnóstico, investigación, solución, reporte")
    print()
    print("🎯 Consultor Full-Stack  — 5 agentes")
    print("   Requerimientos → Arquitectura → Propuesta → Código → Docs")
    print()
    print("Modelos recomendados por agente guardados en .env")
    input("Enter para volver...")

def main():
    while True:
        print_header()
        print("  ¿Qué quieres hacer?")
        print()
        print("  🔍  1) Code Review     — Analizar código fuente")
        print("  🛠️   2) IT Support      — Diagnosticar problema técnico")
        print("  🎯  3) Consultor       — Generar propuesta + código")
        print()
        print("  ⚙️  4) Actualizar .env  — Modelos recomendados")
        print("  📖  5) Acerca de")
        print("  q)   Salir")
        print()
        
        op = input("  Opción: ").strip().lower()
        
        if op == "1":
            code_review()
        elif op == "2":
            it_support()
        elif op == "3":
            consultor()
        elif op == "4":
            update_envs()
            input("\n✅ .env actualizados. Enter...")
        elif op == "5":
            about()
        elif op == "q":
            print("\n👋 Hasta luego!")
            sys.exit(0)
        else:
            input("❌ Opción inválida. Enter...")

if __name__ == "__main__":
    main()
