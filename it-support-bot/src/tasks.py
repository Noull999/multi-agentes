"""Task definitions for IT Support Auto-Pilot."""

from crewai import Task


def create_tasks(agents, issue: str, client: str = "Cliente"):
    """Crea las tareas del pipeline de soporte IT."""

    diagnosticar = Task(
        description=(
            f"Analiza el siguiente problema de soporte IT reportado por {client}:\n\n"
            f"---\n{issue}\n---\n\n"
            "Usa SearchKnowledgeBase para buscar problemas similares. "
            "Identifica: tipo de problema (hardware/software/network/security), "
            "síntomas principales, causas probables ordenadas por probabilidad, "
            "y qué información adicional haría falta para confirmar el diagnóstico."
        ),
        expected_output=(
            "Diagnóstico estructurado: tipo de problema, síntomas identificados, "
            "causas probables (ordenadas por probabilidad), información faltante."
        ),
        agent=agents["diagnostico"],
    )

    investigar = Task(
        description=(
            "Basado en el diagnóstico previo, busca en la web las soluciones más "
            "actualizadas y relevantes. Usa WebSearch para encontrar: "
            "guías oficiales de troubleshooting, foros con el mismo problema resuelto, "
            "parches o actualizaciones disponibles, y workarounds conocidos. "
            "Para cada fuente, evalúa su fiabilidad y relevancia."
        ),
        expected_output=(
            "Lista de soluciones encontradas con: fuente (URL), resumen de la solución, "
            "nivel de confianza (alta/media/baja), y aplicabilidad al caso específico."
        ),
        agent=agents["buscador"],
        context=[diagnosticar],
    )

    resolver = Task(
        description=(
            "Con el diagnóstico y las soluciones investigadas, crea un plan de resolución "
            "paso a paso. El plan debe: "
            "1) Listar los pasos en orden secuencial\n"
            "2) Cada paso debe ser una acción concreta ('Haz clic en X', 'Ejecuta Y')\n"
            "3) Incluir qué resultado esperar después de cada paso\n"
            "4) Tener pasos alternativos si el primario falla\n"
            "5) Indicar cuándo contactar a un nivel de soporte superior\n\n"
            "Usa lenguaje claro, asume que el usuario no es técnico."
        ),
        expected_output=(
            "Plan de resolución paso a paso con: acción, resultado esperado, paso alternativo "
            "si falla, y criterio para escalar."
        ),
        agent=agents["solucionador"],
        context=[diagnosticar, investigar],
    )

    reportar = Task(
        description=(
            f"Genera el reporte final de soporte para {client} usando GenerateSupportReport. "
            "Incluye: descripción del problema original, diagnóstico, pasos realizados, "
            "solución aplicada, y recomendaciones para prevenir que vuelva a ocurrir. "
            "El reporte debe ser profesional y servir como registro del servicio."
        ),
        expected_output=(
            "Reporte de soporte completo guardado en archivo markdown, con todas las "
            "secciones profesionales y contenido accionable."
        ),
        agent=agents["reporteador"],
        context=[diagnosticar, investigar, resolver],
    )

    return [diagnosticar, investigar, resolver, reportar]
