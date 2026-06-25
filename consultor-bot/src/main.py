"""Consultor Full-Stack Automatizado — CLI entry point."""

import logging
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from crewai import LLM
from crew_runner import run_crew
from openai import OpenAI

try:
    from token_tracker import patch_litellm
    patch_litellm(project_name="consultor")
except ImportError:
    pass  # token_tracker opcional (no disponible en Docker sin hermes)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_env() -> None:
    """Load .env with support for quoted values and inline comments."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if val and val[0] in '"\'' and val[-1] == val[0]:
                val = val[1:-1]
            if not (val.startswith('"') or val.startswith("'")):
                val = val.split(" #")[0].split("\t#")[0].strip()
            if key and val:
                os.environ.setdefault(key, val)


def test_llm_connection(api_key: str, base_url: str, model: str) -> bool:
    """Quick test that the LLM endpoint works."""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "respond OK"}],
            max_tokens=5,
        )
        print(f"  LLM OK: {resp.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"  LLM test failed: {e}")
        return False


def main() -> None:
    load_env()

    parser = argparse.ArgumentParser(
        description="Consultor Full-Stack — De la conversación al código",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --input "App web para restaurant" --opencode
  python main.py --input "App mobile" --opencode --model kimi-k2.7-code
  python main.py --file conversacion.txt --opencode
  python main.py --input "App web" --gemini
  python main.py --input "App web" --openai-key sk-...
        """,
    )

    # Input source
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", "-i", help="Descripción del proyecto/cliente")
    source.add_argument("--file", "-f", help="Archivo .txt con la descripción")

    # LLM provider (mutuamente exclusivos, igual que los otros bots)
    provider = parser.add_mutually_exclusive_group()
    provider.add_argument(
        "--opencode",
        action="store_true",
        help="Usar OpenCode Go (default si hay OPENCODE_API_KEY en .env)",
    )
    provider.add_argument(
        "--gemini",
        action="store_true",
        help="Usar Gemini 2.5 Pro (requiere GEMINI_API_KEY)",
    )

    parser.add_argument("--openai-key", help="API key (alternativa a .env)")
    parser.add_argument("--model", default=None, help="Modelo LLM (default según proveedor)")
    parser.add_argument("--base-url", default=None, help="Base URL personalizada")

    args = parser.parse_args()

    # --- Leer input ---
    if args.file:
        fpath = Path(args.file).expanduser().resolve()
        if not fpath.exists():
            print(f"Archivo no encontrado: {fpath}")
            sys.exit(1)
        client_input = fpath.read_text(encoding="utf-8")
        print(f"Leyendo input desde: {fpath}")
    else:
        client_input = args.input

    if not client_input.strip():
        print("Input vacío")
        sys.exit(1)

    # --- Configurar LLM (misma lógica que code-review-bot e it-support-bot) ---
    llm = None

    if args.gemini:
        api_key = args.openai_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Especifica GEMINI_API_KEY en .env o con --openai-key")
            sys.exit(1)
        gemini_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model="openai/gemini-2.5-pro", api_key=api_key, base_url=gemini_base)
        print("Usando Gemini 2.5 Pro")

    elif args.openai_key and not args.opencode:
        # OpenAI nativo si se pasa --openai-key sin --opencode
        api_key = args.openai_key
        model = args.model or os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model=f"openai/{model}", api_key=api_key)
        print(f"Usando OpenAI: {model}")

    else:
        # OpenCode Go (default)
        api_key = args.openai_key or os.getenv("OPENCODE_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("No API key. Agrega OPENCODE_API_KEY en .env o usa --openai-key")
            print('   Ej: python main.py --input "App restaurant" --opencode')
            sys.exit(1)
        base_url = args.base_url or os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
        model = args.model or os.getenv("OPENCODE_MODEL", "glm-5")
        os.environ["OPENAI_API_KEY"] = api_key
        llm = LLM(model=f"openai/{model}", api_key=api_key, base_url=base_url)
        print(f"Usando OpenCode: {model}")
        print(f"Endpoint: {base_url}")

        if not test_llm_connection(api_key, base_url, model):
            print("LLM no responde. Revisa key/modelo.")
            sys.exit(1)

    # --- Ejecutar ---
    try:
        result = run_crew(client_input, llm=llm)
        print("\nResultado final:\n")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
