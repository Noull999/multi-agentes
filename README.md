# Multi-Agentes — Proyectos CrewAI

Proyectos de prueba con sistemas multi-agente usando CrewAI v1.14+.

## Proyectos

| # | Proyecto | Descripción |
|---|---|---|
| 1 | `code-review-bot/` | Revisa código fuente, busca bugs, issues de estilo y sugiere documentación |
| 2 | `it-support-bot/` | Diagnostica problemas IT, busca soluciones y genera reportes de soporte |

## Configuración general

Cada proyecto tiene su propio `.env`. Copia desde `.env.example`:

```bash
cp .env.example .env
# Edita .env con tu API key
```

### Opción A: Gemini (recomendado — gratis)
```
OPENAI_API_KEY=AIzaSy...tu-key-de-gemini
OPENAI_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL_NAME=gemini-2.5-pro
```

### Opción B: OpenAI
```
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL_NAME=gpt-4o
```

### Opción C: Local con Ollama
```
OPENAI_API_KEY=ollama
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_MODEL_NAME=llama4
```

## Cómo ejecutar

```bash
cd code-review-bot
python src/main.py --help
```
