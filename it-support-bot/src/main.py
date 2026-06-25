"""IT Support Auto-Pilot — CLI entry point."""

import logging
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Agregar token_tracker al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from crewai import LLM
from crew_runner import run_crew

try:
    from token_tracker import patch_litellm
    patch_litellm(project_name="it-support")
except ImportError:
    pass  # token_tracker opcional (no disponible en Docker sin hermes)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_env() -> None:
    """Load .env with support for quoted values and inline comments."""
    import shlex
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            # Handle quoted values
            if val and val[0] in '"\'' and val[-1] == val[0]:
                val = val[1:-1]
            # Strip inline comments (only after non-quoted values)
            if not (val.startswith('"') or val.startswith("'")):
                val = val.split(" #")[0].split("\t#")[0].strip()
            if key and val:
                os.environ.setdefault(key, val)


def main() -> None:
    load_env()

    parser = argparse.ArgumentParser(
        description="IT Support Auto-Pilot — Diagnóstico y resolución multi-agente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py "La PC no enciende" --client "Juan Pérez"
  python main.py "Internet lento en oficina" --opencode
  python main.py "Internet lento" --opencode --model deepseek-v4-flash
  python main.py "Pantalla azul al iniciar Windows" --gemini
        """,
    )

    parser.add_argument(
        "issue",
        help="Descripción del problema de soporte",
    )

    parser.add_argument(
        "--client",
        default="Cliente",
        help="Nombre del cliente (opcional)",
    )

    parser.add_argument(
        "--opencode",
        action="store_true",
        help="Usar OpenCode (OpenAI-compatible) como LLM",
    )

    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Usar Gemini (OpenAI-compatible) como LLM",
    )

    parser.add_argument(
        "--openai-key",
        help="API key de OpenAI/Gemini/OpenCode (alternativa a .env)",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Modelo a usar con --opencode (default: glm-5)",
    )

    args = parser.parse_args()

    # --- Configurar LLM ---
    llm = None

    if args.opencode:
        api_key = args.openai_key or os.getenv("OPENCODE_API_KEY")
        if not api_key:
            print("❌ Especifica OPENCODE_API_KEY en .env o con --openai-key")
            sys.exit(1)
        model = args.model or os.getenv("OPENCODE_MODEL", "glm-5")
        base_url = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
        os.environ["OPENAI_API_KEY"] = api_key
        # "openai/" prefix tells LiteLLM to use OpenAI provider with custom base_url.
        # Without it, LiteLLM returns a raw string instead of ModelResponse,
        # causing AttributeError: 'str' object has no attribute 'choices'.
        llm = LLM(model=f"openai/{model}", api_key=api_key, base_url=base_url)
        print(f"🧠 Usando OpenCode: {model} -> {base_url}")

    elif args.gemini:
        api_key = args.openai_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Especifica GEMINI_API_KEY en .env o con --openai-key")
            sys.exit(1)
        gemini_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model="openai/gemini-2.5-pro", api_key=api_key, base_url=gemini_base)
        print("🧠 Usando Gemini 2.5 Pro")

    elif args.openai_key or os.getenv("OPENAI_API_KEY"):
        api_key = args.openai_key or os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model=f"openai/{model}", api_key=api_key)
        print(f"🧠 Usando OpenAI: {model}")

    else:
        print("⚠️  No se configuró LLM. Usa --opencode / --gemini / --openai-key")
        print('   Ej: python main.py "PC no enciende" --opencode')
        sys.exit(1)

    # --- Ejecutar ---
    try:
        result = run_crew(args.issue, llm=llm)
        print("\n📋 Resultado final:\n")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
