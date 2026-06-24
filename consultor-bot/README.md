# Consultor Bot

**Consultor Full-Stack Automatizado** — Un pipeline multi-agente que transforma la descripción de un proyecto (en lenguaje natural) en una propuesta profesional, arquitectura técnica, código base y documentación.

> ⚡ De la conversación al código, en minutos.

---

## ✨ ¿Qué hace?

1. **Analiza** la descripción del cliente y extrae requerimientos estructurados.
2. **Diseña** la arquitectura técnica óptima (stack, diagrama, DB, endpoints).
3. **Propone** una propuesta comercial profesional en markdown.
4. **Genera** el proyecto base (Next.js, FastAPI o full-stack) con código funcional.
5. **Documenta** el proyecto (README, setup, deploy).

Todo orquestado con **CrewAI** y modelos LLM vía endpoint OpenAI-compatible.

---

## 🧠 Agentes

| Agente | Rol | Herramientas |
|--------|-----|-------------|
| **Analista** | Requeriments Analyst | — |
| **Arquitecto** | Solution Architect | ScaffoldProject |
| **Redactor** | Proposal Writer | GenerateProposalDocument |
| **Generador** | Code Generator | ScaffoldProject, GenerateCodeFile |
| **Documentador** | Documentation Writer | GenerateCodeFile |

---

## 🚀 Uso rápido

```bash
# 1. Clonar y entrar
git clone <repo> && cd consultor-bot

# 2. Entorno virtual
python3 -m venv .venv && source .venv/bin/activate

# 3. Instalar
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env con OPENCODE_API_KEY, OPENCODE_MODEL, etc.

# 5. Ejecutar
cd src
python main.py --input "Necesito una app web para control de inventario..."
```

O desde un archivo de texto:

```bash
python main.py --file conversacion.txt
```

---

## ⚙️ Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OPENCODE_API_KEY` | — | API key del endpoint LLM |
| `OPENCODE_MODEL` | `glm-5` | Modelo a usar |
| `OPENCODE_BASE_URL` | `https://opencode.ai/zen/go/v1` | Endpoint OpenAI-compatible |
| `CONSULTOR_OUTPUT` | `./output` | Directorio donde se escriben propuestas y proyectos |

---

## 📁 Estructura del proyecto

```
consultor-bot/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── crew_runner.py          # Orquestación del pipeline CrewAI
│   ├── agents.py               # Definición de los 5 agentes
│   ├── tasks.py                # Definición de las 5 tareas
│   └── tools/
│       ├── __init__.py
│       └── project_tools.py    # Herramientas: scaffold, proposal, codegen
├── tests/
│   └── test_tools.py           # Tests de herramientas
├── output/                     # Propuestas y proyectos generados (gitignored)
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🧪 Tests

```bash
# Desde la raíz del proyecto
source .venv/bin/activate
pip install pytest pytest-env
pytest tests/ -v
```

Los tests cubren:
- Path traversal en `scaffold_project` y `generate_code_file`
- Sanitización de nombres de proyecto
- Escritura de propuestas dentro de `OUTPUT_BASE`
- Timeline corto (≤2 semanas) no crashea

---

## 🛡️ Seguridad

- Todas las rutas de archivos se resuelven contra `OUTPUT_BASE` y se verifica que no escapen.
- Los nombres de proyecto son sanitizados (solo `[a-zA-Z0-9_\-]`).
- Path traversal es bloqueado en `scaffold_project` y `generate_code_file`.
- `CONSULTOR_OUTPUT` se valida contra la raíz del proyecto.

---

## 📝 Licencia

MIT © José Asencio Barrientos
