# 🛠️ IT Support Auto-Pilot

**Sistema multi-agente para diagnóstico y resolución automatizada de problemas de soporte técnico IT.**

---

## 🔍 ¿Qué hace?

IT Support Auto-Pilot es un pipeline de 4 agentes inteligentes (basados en CrewAI) que trabajan en secuencia para:

1. **Diagnostic Technician** — Analiza el problema reportado, identifica síntomas y causas probables usando una base de conocimiento local.
2. **Technical Research Specialist** — Busca soluciones actualizadas en la web (DuckDuckGo API) para complementar el diagnóstico.
3. **Solution Builder** — Genera un plan de resolución paso a paso, con alternativas y criterios de escalamiento.
4. **Support Report Writer** — Compila un reporte profesional en Markdown con todo el proceso documentado.

El resultado es un reporte completo en `./reports/` que puede compartirse con el cliente y archivarse como registro.

---

## 🚀 Requisitos

- **Python 3.11+**
- **CrewAI** (instalado automáticamente)
- Una **API key** de alguno de los proveedores LLM soportados

## ⚙️ Instalación

```bash
# Clonar el repositorio
git clone https://github.com/nousresearch/it-support-bot.git
cd it-support-bot

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 🔐 Configuración

Copia `.env.example` a `.env` y configura al menos una API key:

```bash
cp .env.example .env
```

Opciones disponibles en `.env`:

| Variable              | Descripción                          | Requerido para       |
|-----------------------|--------------------------------------|----------------------|
| `OPENAI_API_KEY`      | API key de OpenAI                    | OpenAI               |
| `OPENCODE_API_KEY`    | API key de OpenCode.ai               | `--opencode`         |
| `OPENCODE_MODEL`      | Modelo OpenCode (default: glm-5)     | `--opencode`         |
| `OPENCODE_BASE_URL`   | URL base OpenCode                    | `--opencode`         |
| `GEMINI_API_KEY`      | API key de Gemini                    | `--gemini`           |
| `IT_SUPPORT_OUTPUT`   | Directorio de reportes (default: ./reports) | Opcional    |

## 🧠 Uso

Desde la raíz del proyecto:

```bash
python src/main.py "Descripción del problema" --client "Nombre del Cliente"
```

### Ejemplos

```bash
# Usar OpenAI (por defecto si OPENAI_API_KEY está configurada)
python src/main.py "La PC no enciende" --client "Juan Pérez"

# Usar OpenCode.ai
python src/main.py "Internet lento en oficina" --opencode

# Usar OpenCode con modelo específico
python src/main.py "Internet lento" --opencode --model deepseek-v4-flash

# Usar Gemini
python src/main.py "Pantalla azul al iniciar Windows" --gemini

# Especificar API key directamente
python src/main.py "Correo no envía" --openai-key "sk-..."
```

### Proveedores LLM

| Flag           | Provider        | LLM por defecto         |
|----------------|-----------------|-------------------------|
| *(ninguno)*    | OpenAI          | `gpt-4o`                |
| `--opencode`   | OpenCode.ai     | `glm-5`                 |
| `--gemini`     | Gemini          | `gemini-2.5-pro`        |

## 🧪 Tests

```bash
# Activar el entorno virtual
source .venv/bin/activate

# Instalar dependencias de desarrollo
pip install pytest pytest-cov

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=src --cov-report=term-missing
```

## 📁 Estructura del proyecto

```
it-support-bot/
├── src/
│   ├── main.py                  # Punto de entrada CLI
│   ├── crew_runner.py           # Orquestador CrewAI
│   ├── agents.py                # Definición de agentes
│   ├── tasks.py                 # Definición de tareas
│   └── tools/
│       ├── __init__.py
│       ├── web_search.py        # Búsqueda web (DuckDuckGo) + KB local
│       └── report_generator.py  # Generación de reportes Markdown
├── tests/
│   └── test_tools.py            # Tests unitarios
├── reports/                     # Reportes generados (gitignored)
├── .env                         # Variables de entorno (no incluir en git)
├── .env.example                 # Plantilla para .env
├── pyproject.toml               # Configuración del proyecto
├── requirements.txt             # Dependencias
└── README.md                    # Este archivo
```

## 🛡️ Seguridad

- **Path traversal sanitization**: El nombre del cliente se sanitiza con una expresión regular que elimina caracteres peligrosos (`../`, `./`, etc.) antes de usarlo en nombres de archivo.
- **HTML injection prevention**: Los caracteres `<` y `>` se escapan a `&lt;` y `&gt;` en los reportes.
- **Error message safety**: Los mensajes de error no filtran contenido sensible del reporte.
- **Prompt injection defense**: El input del usuario se delimita con marcadores `INICIO/FIN REPORTE CLIENTE` y se instruye a los agentes a no ejecutar instrucciones incrustadas.

## 📄 Licencia

MIT
