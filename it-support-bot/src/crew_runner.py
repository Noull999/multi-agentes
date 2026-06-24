"""Crew runner — orchestrate the IT Support agents."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from crewai import Crew, LLM, Process

logger = logging.getLogger(__name__)


def run_crew(issue: str, llm: Optional[LLM] = None) -> str:
    """Ejecuta el crew de soporte IT completo."""

    from agents import create_agents
    from tasks import create_tasks

    print(f"\n🛠️  Iniciando soporte IT\n")
    print(f"📝 Problema: {issue[:100]}...\n")

    agents = create_agents(llm=llm)
    tasks = create_tasks(agents, issue)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        print(f"\n✅ Soporte IT completado.\n")
        return result
    except Exception as e:
        logger.exception("Soporte IT falló")
        error_msg = f"❌ Soporte IT falló: {e}"
        print(error_msg)
        return error_msg
