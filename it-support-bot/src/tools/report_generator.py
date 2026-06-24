"""Tool: generate professional IT support reports."""

from datetime import datetime
from crewai.tools import tool


@tool("GenerateSupportReport")
def generate_support_report(
    client_name: str,
    issue_description: str,
    diagnosis: str,
    solution: str,
    steps_performed: str,
    recommendations: str = "",
) -> str:
    """
    Genera un reporte profesional de soporte IT.
    Recibe: nombre del cliente, descripción del problema, diagnóstico,
    solución aplicada, pasos realizados y recomendaciones adicionales.
    Devuelve la ruta del archivo generado.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"soporte-{client_name.lower().replace(' ', '-')}-{report_id}.md"

    report = f"""# 🛠️ Reporte de Soporte Técnico

**Cliente:** {client_name}
**Fecha:** {timestamp}
**Reporte ID:** {report_id}

---

## 📋 Descripción del Problema

{issue_description}

---

## 🔍 Diagnóstico

{diagnosis}

---

## ✅ Solución Aplicada

{solution}

---

## 📝 Pasos Realizados

{steps_performed}

---

## 💡 Recomendaciones

{recommendations if recommendations else "Sin recomendaciones adicionales."}

---

*Reporte generado automáticamente por IT Support Auto-Pilot Agent.*
"""

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        return f"✅ Reporte guardado: {filename}"
    except Exception as e:
        return f"⚠️ Error guardando reporte: {e}\n\n---\n{report}"
