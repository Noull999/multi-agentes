"""Crew runner — orchestrate the code review agents."""

import logging
from typing import Any, Optional

from crewai import Crew, Process

logger = logging.getLogger(__name__)


def run_crew(target_dir: str, llm: Optional[Any] = None) -> str:
    """Ejecuta el crew de code review completo.

    Args:
        target_dir: Directorio del proyecto a analizar.
        llm: Instancia opcional de crewai.LLM para usar como modelo.

    Returns:
        Resultado del crew (string con el reporte).
    """

    # Importar agentes y tareas ACÁ para evitar carga circular
    from agents import create_agents
    from tasks import create_tasks

    print(f"\n🔍 Iniciando Code Review para: {target_dir}\n")

    # Crear agentes (pasar LLM si se configuró)
    agents = create_agents(llm=llm)

    # Crear tareas
    tasks = create_tasks(agents, target_dir)

    # Crear y ejecutar crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        print(f"\n✅ Code Review completado.\n")
        return result
    except Exception as e:
        logger.exception("Code Review falló")
        error_msg = f"❌ Code Review falló: {e}"
        print(error_msg)
        return error_msg
