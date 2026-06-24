"""Crew runner — orchestrate the consultant agents."""

import logging
import os
from pathlib import Path
from typing import Any

from crewai import Crew, Process

logger = logging.getLogger(__name__)


def run_crew(client_input: str, llm: Any = None) -> str:
    """Ejecuta el pipeline completo de consultoría."""

    from agents import create_agents
    from tasks import create_tasks

    preview = client_input[:120].replace("\n", " ")
    print(f"\n📋 Iniciando consultoría para:\n   \"{preview}...\"\n")

    agents = create_agents(llm=llm)
    tasks = create_tasks(agents, client_input)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        print(f"\n✅ Pipeline de consultoría completado.\n")
        return result
    except Exception as e:
        logger.exception("Pipeline de consultoría falló")
        error_msg = f"❌ Pipeline de consultoría falló: {e}"
        print(error_msg)
        return error_msg
