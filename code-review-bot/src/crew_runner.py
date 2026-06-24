"""Crew runner — orchestrate the code review agents."""

import os
import sys
from pathlib import Path

from crewai import Crew, Process


def run_crew(target_dir: str, llm=None) -> str:
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

    result = crew.kickoff()

    print(f"\n✅ Code Review completado.\n")
    return result
