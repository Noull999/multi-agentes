"""Crew runner — orchestrate the consultant agents."""

import os
from pathlib import Path

from crewai import Crew, Process


def run_crew(client_input: str, llm=None) -> str:
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

    result = crew.kickoff()

    print(f"\n✅ Pipeline de consultoría completado.\n")
    return result
