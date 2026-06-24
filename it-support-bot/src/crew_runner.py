"""Crew runner — orchestrate the IT Support agents."""

import os
import sys
from pathlib import Path

from crewai import Crew, Process


def run_crew(issue: str, llm=None) -> str:
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

    result = crew.kickoff()

    print(f"\n✅ Soporte IT completado.\n")
    return result
