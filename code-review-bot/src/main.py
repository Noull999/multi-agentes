"""Code Review Bot — CLI entry point."""

import os
import sys
import argparse
from pathlib import Path

# Ensure src directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crewai import LLM
from crew_runner import run_crew


def load_env():
    """Load .env if it exists."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def test_llm_connection(api_key: str, base_url: str, model: str) -> bool:
    """Quick test that the LLM endpoint works."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "respond OK"}],
            max_tokens=5,
        )
        print(f"  ✅ LLM OK: {resp.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"  ❌ LLM test failed: {e}")
        return False


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Code Review Bot — Revisión multi-agente de código fuente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py ~/projects/predial-lechero
  python main.py . --openai-key sk-...
  python main.py /ruta/al/proyecto --gemini
  python main.py /ruta/al/proyecto --opencode
  python main.py /ruta/al/proyecto --opencode --model deepseek-v4-flash
    """,
    )

    parser.add_argument(
        "directory",
        help="Ruta del proyecto a analizar",
    )

    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Usar Gemini (OpenAI-compatible) como LLM",
    )

    parser.add_argument(
        "--opencode",
        action="store_true",
        help="Usar OpenCode Go (glm-5 / deepseek-v4-flash / kimi-k2.6)",
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

    # --- Configurar LLM usando crewai.LLM con prefijo openai/ ---
    # The "openai/" prefix tells LiteLLM to use OpenAI provider with custom base_url.
    # Without it, LiteLLM returns str instead of ModelResponse → AttributeError
    llm = None

    if args.opencode:
        api_key = args.openai_key or os.getenv("OPENCODE_API_KEY")
        if not api_key:
            print("❌ Especifica OPENCODE_API_KEY en .env o con --openai-key")
            sys.exit(1)
        model = args.model or os.getenv("OPENCODE_MODEL", "glm-5")
        base_url = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model=f"openai/{model}", api_key=api_key, base_url=base_url)
        print(f"🧠 Usando OpenCode: {model} → {base_url}")

        # Quick connection test
        if not test_llm_connection(api_key, base_url, model):
            print("❌ OpenCode LLM no responde. Revisa key/modelo.")
            sys.exit(1)

    elif args.gemini:
        api_key = args.openai_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Especifica GEMINI_API_KEY en .env o con --openai-key")
            sys.exit(1)
        gemini_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = gemini_base
        llm = LLM(model="openai/gemini-2.5-pro", api_key=api_key, base_url=gemini_base)
        print("🧠 Usando Gemini 2.5 Pro")

    elif args.openai_key or os.getenv("OPENAI_API_KEY"):
        api_key = args.openai_key or os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model=f"openai/{model}", api_key=api_key, base_url=base_url)
        print(f"🧠 Usando OpenAI: {model}")

    else:
        print("⚠️  No se configuró LLM. Revisa .env o usa --opencode / --gemini / --openai-key")
        print("   Ej: python main.py /ruta/proyecto --opencode")
        sys.exit(1)

    # --- Resolver directorio ---
    target = os.path.expanduser(args.directory)
    if not os.path.isdir(target):
        print(f"❌ El directorio '{target}' no existe o no es accesible.")
        sys.exit(1)

    # --- Ejecutar ---
    result = run_crew(target, llm=llm)

    print("\n📋 Resultado final:\n")
    print(result)


if __name__ == "__main__":
    main()
