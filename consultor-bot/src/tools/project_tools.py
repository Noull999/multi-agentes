"""Tools: proposal generation, project scaffolding, code generation."""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from crewai.tools import tool

# Output directory — sandboxed. All writes stay inside this root.
_CONSULTOR_ROOT = Path(__file__).resolve().parent.parent.parent  # project root
_OUTPUT_ENV = os.getenv("CONSULTOR_OUTPUT", "./output")
OUTPUT_BASE = Path(_OUTPUT_ENV).resolve()
# P0: constrain to project root — reject env var paths that escape
try:
    OUTPUT_BASE.relative_to(_CONSULTOR_ROOT)
except ValueError:
    OUTPUT_BASE = _CONSULTOR_ROOT / "output"
    print(f"⚠️ CONSULTOR_OUTPUT='{_OUTPUT_ENV}' escapa del proyecto. Usando: {OUTPUT_BASE}")


@tool("GenerateProposalDocument")
def generate_proposal_document(
    client_name: str,
    project_name: str,
    executive_summary: str,
    scope: str,
    tech_stack: str,
    timeline_weeks: int,
    budget: str,
    terms: str = "",
) -> str:
    """
    Genera una propuesta profesional en markdown para presentar a un cliente.
    Devuelve la ruta del archivo generado.
    """
    timestamp = datetime.now()

    # P0: sanitize project_name to prevent path traversal
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', project_name)[:60].strip().lower().replace(' ', '-')
    if not safe_name:
        safe_name = "proyecto"

    # Include seconds to avoid overwrite on same-day runs
    filename = f"propuesta-{safe_name}-{timestamp.strftime('%Y%m%d_%H%M%S')}.md"

    # f-strings can't contain triple-quoted strings (SyntaxError in Python < 3.12)
    default_terms = (
        "- 2 rondas de correcciones incluidas\n"
        "- Soporte post-entrega: 1 semana\n"
        "- Hosting no incluido en el presupuesto\n"
        "- Pago en CLP via transferencia / PayPal"
    )
    terms_text = terms if terms else default_terms

    # P1: fix milestone dates for short timelines
    timeline_weeks = max(timeline_weeks, 1) if isinstance(timeline_weeks, int) else 4
    start_date = timestamp + timedelta(days=3)
    end_date = start_date + timedelta(weeks=timeline_weeks)
    milestones = []
    if timeline_weeks >= 3:
        for i in range(1, 4):
            ms_date = start_date + timedelta(weeks=(timeline_weeks // 3) * i)
            milestones.append(f"  - Hito {i}: {ms_date.strftime('%d/%m/%Y')}")
    else:
        # For short timelines, distribute milestones proportionally
        mid = start_date + timedelta(weeks=timeline_weeks // 2)
        milestones = [
            f"  - Hito 1: {mid.strftime('%d/%m/%Y')}",
            f"  - Entrega final: {end_date.strftime('%d/%m/%Y')}",
        ]

    doc = f"""# Propuesta Técnica: {project_name}

**Cliente:** {client_name}
**Fecha:** {timestamp.strftime('%d/%m/%Y')}
**Propuesta válida hasta:** {(timestamp + timedelta(days=15)).strftime('%d/%m/%Y')}

---

## 1. Resumen Ejecutivo

{executive_summary}

---

## 2. Alcance del Proyecto

{scope}

---

## 3. Stack Tecnológico Propuesto

{tech_stack}

---

## 4. Entregables

- Aplicación funcional deployada
- Código fuente en repositorio privado
- Documentación técnica y de usuario
- Transferencia de conocimiento (sesión 1hr)

---

## 5. Cronograma

- **Inicio:** {start_date.strftime('%d/%m/%Y')}
- **Desarrollo:** {timeline_weeks} semanas ({start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')})
{chr(10).join(milestones)}
- **Entrega final:** {end_date.strftime('%d/%m/%Y')}

---

## 6. Presupuesto

{budget}

**Forma de pago sugerida:**
- 50% al inicio (para partir)
- 25% al hito 2 (mitad del proyecto)
- 25% contra entrega final

---

## 7. Términos y Condiciones

{terms_text}

---

## 8. Sobre el Desarrollador

**José Asencio Barrientos**
Full-Stack Developer · Puerto Montt, Chile
- Stack: TypeScript, Next.js, React, Python, PostgreSQL
- Experiencia: Apps web, automatización, soporte IT
- Portfolio: https://portfolio-v4-rho-opal.vercel.app

---

*Propuesta generada automáticamente con asistencia de IA.*
"""

    try:
        OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_BASE / filename
        # P0: verify resolved path stays inside OUTPUT_BASE
        if not out_path.resolve().is_relative_to(OUTPUT_BASE.resolve()):
            raise ValueError("Path escapes output directory")
        out_path.write_text(doc, encoding="utf-8")
        return f"✅ Propuesta generada: {out_path}"
    except Exception as e:
        # P1: don't leak document content in error
        return f"⚠️ Error generando propuesta: {e}"


@tool("ScaffoldProject")
def scaffold_project(
    project_name: str,
    tech_stack: str,
    project_type: str = "nextjs",
) -> str:
    """
    Crea la estructura base de un proyecto de software.
    Soporta: nextjs, fastapi, nextjs-fastapi.
    Devuelve la ruta y el árbol de directorios creado.
    """
    # P0: sanitize project_name and restrict to OUTPUT_BASE
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '-', project_name)[:60].strip()
    if not safe_name:
        return "⚠️ Invalid project name"
    base = (OUTPUT_BASE / safe_name).resolve()
    if not base.is_relative_to(OUTPUT_BASE.resolve()):
        return "⚠️ Path escapes output directory"
    if base.exists():
        return f"⚠️ Ya existe un directorio '{base}'"

    structure = {}

    if project_type == "nextjs":
        structure = {
            f"{project_name}/": None,
            f"{project_name}/src/app/": None,
            f"{project_name}/src/app/api/": None,
            f"{project_name}/src/components/": None,
            f"{project_name}/src/lib/": None,
            f"{project_name}/src/types/": None,
            f"{project_name}/public/": None,
            f"{project_name}/tests/": None,
        }
        boot_files = {
            f"{project_name}/package.json": json_template("nextjs", project_name),
            f"{project_name}/tsconfig.json": "{\n  \"compilerOptions\": {\n    \"target\": \"ES2017\",\n    \"lib\": [\"dom\", \"dom.iterable\", \"esnext\"],\n    \"allowJs\": true,\n    \"skipLibCheck\": true,\n    \"strict\": true,\n    \"noEmit\": true,\n    \"esModuleInterop\": true,\n    \"module\": \"esnext\",\n    \"moduleResolution\": \"bundler\",\n    \"resolveJsonModule\": true,\n    \"isolatedModules\": true,\n    \"jsx\": \"preserve\",\n    \"incremental\": true,\n    \"plugins\": [{\"name\": \"next\"}],\n    \"paths\": {\"@/*\": [\"./src/*\"]}\n  },\n  \"include\": [\"next-env.d.ts\", \"**/*.ts\", \"**/*.tsx\", \".next/types/**/*.ts\"],\n  \"exclude\": [\"node_modules\"]\n}",
            f"{project_name}/next.config.ts": "import type { NextConfig } from 'next';\n\nconst nextConfig: NextConfig = {\n  /* config here */\n};\n\nexport default nextConfig;\n",
            f"{project_name}/src/app/layout.tsx": "import type { Metadata } from 'next';\n\nexport const metadata: Metadata = {\n  title: '{{PROJECT_NAME}}',\n  description: 'Generated with AI assistance',\n};\n\nexport default function RootLayout({ children }: { children: React.ReactNode }) {\n  return (\n    <html lang='es'>\n      <body>{children}</body>\n    </html>\n  );\n}\n",
            f"{project_name}/src/app/page.tsx": "export default function Home() {\n  return (\n    <main>\n      <h1>{{PROJECT_NAME}}</h1>\n      <p>Proyecto generado con asistencia de IA.</p>\n    </main>\n  );\n}\n",
            f"{project_name}/.gitignore": "node_modules\n.next\n.env.local\n*.tsbuildinfo\nnext-env.d.ts\n",
            f"{project_name}/README.md": f"# {project_name}\n\n{tech_stack}\n\n## Getting Started\n\n```bash\npnpm install\npnpm dev\n```\n",
        }
    elif project_type == "fastapi":
        structure = {
            f"{project_name}/": None,
            f"{project_name}/app/": None,
            f"{project_name}/app/api/": None,
            f"{project_name}/app/models/": None,
            f"{project_name}/app/schemas/": None,
            f"{project_name}/app/services/": None,
            f"{project_name}/app/core/": None,
            f"{project_name}/tests/": None,
        }
        boot_files = {
            f"{project_name}/requirements.txt": "fastapi>=0.115.0\nuvicorn[standard]>=0.34.0\npydantic>=2.0.0\nsqlalchemy>=2.0.0\n",
            f"{project_name}/app/__init__.py": "",
            f"{project_name}/app/main.py": "from fastapi import FastAPI\n\napp = FastAPI(title='{{PROJECT_NAME}}')\n\n@app.get('/')\ndef root():\n    return {'message': '{{PROJECT_NAME}} API'}\n",
            f"{project_name}/app/core/__init__.py": "",
            f"{project_name}/app/core/config.py": "from pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    app_name: str = '{{PROJECT_NAME}}'\n    debug: bool = True\n\n    class Config:\n        env_file = '.env'\n\nsettings = Settings()\n",
            f"{project_name}/.gitignore": "__pycache__\n*.pyc\n.env\n.venv\n",
        }

    else:  # nextjs-fastapi (full-stack)
        structure = {
            f"{project_name}/": None,
            f"{project_name}/frontend/": None,
            f"{project_name}/frontend/src/app/": None,
            f"{project_name}/frontend/src/components/": None,
            f"{project_name}/frontend/src/lib/": None,
            f"{project_name}/frontend/public/": None,
            f"{project_name}/backend/": None,
            f"{project_name}/backend/app/api/": None,
            f"{project_name}/backend/app/models/": None,
            f"{project_name}/backend/app/core/": None,
            f"{project_name}/backend/tests/": None,
            f"{project_name}/docs/": None,
        }
        boot_files = {
            f"{project_name}/README.md": f"# {project_name}\n\nFull-stack project: Next.js (frontend) + FastAPI (backend).\n\n{tech_stack}\n",
            f"{project_name}/frontend/package.json": json_template("nextjs", f"{project_name}-frontend"),
            f"{project_name}/frontend/src/app/page.tsx": "export default function Home() {\n  return <h1>{{PROJECT_NAME}} - Frontend</h1>;\n}\n",
            f"{project_name}/backend/requirements.txt": "fastapi>=0.115.0\nuvicorn>=0.34.0\npydantic>=2.0.0\n",
            f"{project_name}/backend/app/__init__.py": "",
            f"{project_name}/backend/app/main.py": "from fastapi import FastAPI\n\napp = FastAPI(title='{{PROJECT_NAME}} API')\n\n@app.get('/api/health')\ndef health():\n    return {'status': 'ok'}\n",
            f"{project_name}/.gitignore": "node_modules\n.next\n.venv\n__pycache__\n.env.local\n.env\n",
            f"{project_name}/docker-compose.yml": "version: '3.9'\nservices:\n  backend:\n    build: ./backend\n    ports:\n      - '8000:8000'\n  frontend:\n    build: ./frontend\n    ports:\n      - '3000:3000'\n    depends_on:\n      - backend\n",
        }

    # Crear directorios — siempre bajo OUTPUT_BASE
    created_dirs = []
    for dirpath in structure:
        full = (OUTPUT_BASE / dirpath).resolve()
        if not full.is_relative_to(OUTPUT_BASE.resolve()):
            continue  # no debería pasar, pero por seguridad
        full.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dirpath)

    # Crear archivos base — siempre bajo OUTPUT_BASE
    created_files = []
    for fpath, content in boot_files.items():
        content = content.replace("{{PROJECT_NAME}}", project_name)
        full = (OUTPUT_BASE / fpath).resolve()
        if not full.is_relative_to(OUTPUT_BASE.resolve()):
            continue
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        created_files.append(fpath)

    tree = [f"📁 {project_name}/  (guardado en {OUTPUT_BASE / safe_name})"]
    for d in sorted(created_dirs):
        try:
            rel = Path(d).relative_to(project_name)
            indent = "  " * len(rel.parts)
            tree.append(f"{indent}📁 {Path(d).name}/")
        except ValueError:
            pass
    for f in sorted(created_files):
        try:
            rel = Path(f).relative_to(project_name)
            indent = "  " * (len(rel.parents) - 1)
            tree.append(f"{indent}📄 {rel.name}")
        except ValueError:
            pass

    return f"✅ Proyecto '{project_name}' creado ({project_type})\n\n" + "\n".join(tree)


@tool("GenerateCodeFile")
def generate_code_file(filepath: str, code_content: str) -> str:
    """
    Crea o sobrescribe un archivo de código con el contenido especificado.
    Recibe: ruta del archivo y contenido completo (relativo a OUTPUT_BASE).
    Útil para: crear componentes, APIs, schemas, tests, etc.
    """
    if not filepath or not code_content:
        return "❌ Error: filepath y code_content son requeridos"

    # P0: sanitize path — restrict to OUTPUT_BASE
    # Remove leading ../ or / to prevent traversal
    clean_path = filepath.lstrip("/").lstrip("\\")
    path = (OUTPUT_BASE / clean_path).resolve()
    if not path.is_relative_to(OUTPUT_BASE.resolve()):
        return "❌ Error: la ruta escapa del directorio de salida permitido"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code_content, encoding="utf-8")
        return f"✅ Archivo creado: {path} ({len(code_content)} bytes)"
    except Exception as e:
        # P1: raise so CrewAI surfaces the failure
        from crewai.tools import ToolException
        raise ToolException(f"Error creando archivo: {e}") from e


# Helper
def json_template(project_type: str, name: str) -> str:
    if project_type == "nextjs":
        return json.dumps({
            "name": name,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
            },
            "dependencies": {
                "next": "^15.2.0",
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
            },
            "devDependencies": {
                "@types/node": "^22.0.0",
                "@types/react": "^19.0.0",
                "@types/react-dom": "^19.0.0",
                "typescript": "^5.7.0",
            },
        }, indent=2)
    return "{}"
