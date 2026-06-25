"""Consultor Full-Stack Automatizado — CLI entry point."""

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
from openai import OpenAI

try:
    from token_tracker import patch_litellm
    patch_litellm(project_name="consultor")
except ImportError:
    pass  # token_tracker opcional (no disponible en Docker sin hermes)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_env() -> None:
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


def main() -> None:
    load_env()

    parser = argparse.ArgumentParser(
        description="Consultor Full-Stack — De la conversación al código",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --input "Cliente necesita app web para control de produccion agricola..."
  python main.py --file conversacion.txt
  python main.py --input "App mobile" --model deepseek-v4-flash
  python main.py --input "App mobile" --model kimi-k2.6
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", "-i", help="Descripción del proyecto/cliente")
    source.add_argument("--file", "-f", help="Archivo .txt con la descripción")

    parser.add_argument("--model", default=None, help="Modelo (default: OPENCODE_MODEL)")
    parser.add_argument("--base-url", default=None, help="Base URL (default: OPENCODE_BASE_URL)")

    args = parser.parse_args()

    # --- Read input ---
    if args.file:
        fpath = Path(args.file).expanduser().resolve()
        if not fpath.exists():
            print(f"❌ Archivo no encontrado: {fpath}")
            sys.exit(1)
        client_input = fpath.read_text(encoding="utf-8")
        print(f"📄 Leyendo input desde: {fpath}")
    else:
        client_input = args.input

    if not client_input.strip():
        print("❌ Input vacío")
        sys.exit(1)

    # --- Read config from .env ---
    api_key = os.getenv("OPENCODE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found. Set OPENCODE_API_KEY in .env")
        sys.exit(1)

    base_url = args.base_url or os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
    model = args.model or os.getenv("OPENCODE_MODEL", "glm-5")

    print(f"🧠 OpenCode: {model}")
    print(f"🔗 Endpoint: {base_url}")

    # --- Test connection ---
    if not test_llm_connection(api_key, base_url, model):
        print("❌ LLM no responde. Revisa key/modelo.")
        sys.exit(1)

    # Build the LLM object — crewai.LLM + "openai/" prefix is required for
    # LiteLLM to route custom OpenAI-compatible endpoints correctly.
    # Without the prefix, LiteLLM returns a raw string instead of ModelResponse,
    # causing AttributeError: 'str' object has no attribute 'choices'.
    os.environ["OPENAI_API_KEY"] = api_key
    llm = LLM(model=f"openai/{model}", api_key=api_key, base_url=base_url)

    # --- Ejecutar ---
    try:
        result = run_crew(client_input, llm=llm)
        print("\n📋 Resultado final:\n")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
