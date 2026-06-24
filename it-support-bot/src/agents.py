"""Agent definitions for IT Support Auto-Pilot."""

from typing import Optional

from crewai import Agent, LLM
from tools.web_search import web_search, search_knowledge_base
from tools.report_generator import generate_support_report


def create_agents(llm: Optional[LLM] = None) -> dict[str, Agent]:
    """Crea los 4 agentes del IT Support Auto-Pilot."""

    shared_config = {}
    if llm:
        shared_config["llm"] = llm

    diagnostico = Agent(
        role="Diagnostic Technician",
        goal=(
            "Analyze IT issues described by the client, ask clarifying questions, "
            "identify the root cause based on symptoms, and categorize the problem "
            "(network, hardware, software, printer, security, etc.). "
            "Provide a structured diagnosis with probable causes ordered by likelihood."
        ),
        backstory=(
            "You are a senior IT support technician with 10+ years of experience "
            "troubleshooting everything from Windows blue screens to Linux server failures. "
            "You're known for your methodical approach: you never jump to conclusions, "
            "you rule out the simple causes first, and you always have aPlan B, C and D. "
            "You speak in clear, actionable language."
        ),
        tools=[search_knowledge_base],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    buscador = Agent(
        role="Technical Research Specialist",
        goal=(
            "Search the web for solutions to technical problems. Find the most relevant, "
            "up-to-date, and reliable sources for troubleshooting steps, driver updates, "
            "known issues, and best practices. Prioritize official documentation, "
            "Microsoft/Apple/Linux forums, and reputable tech sites."
        ),
        backstory=(
            "You are a world-class Googler. When something breaks, you can find the fix "
            "in minutes while others are still trying to describe the problem. You know "
            "the right keywords, you can spot outdated solutions, and you always verify "
            "that a solution actually applies to the specific version/OS the client has."
        ),
        tools=[web_search],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    solucionador = Agent(
        role="Solution Builder",
        goal=(
            "Take the diagnosis and research findings and create a clear, step-by-step "
            "resolution plan. Each step must be specific, actionable, and ordered. "
            "Include expected results after each step so the client knows if they're "
            "on the right track. Define alternative steps in case primary solution fails."
        ),
        backstory=(
            "You excel at turning technical research into easy-to-follow procedures. "
            "You've written documentation for help desks and know that the best solution "
            "is useless if the client can't follow it. You assume the client has basic "
            "computer skills but may not know technical jargon — you use plain language "
            "with technical terms explained in parentheses."
        ),
        tools=[web_search],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    reporteador = Agent(
        role="Support Report Writer",
        goal=(
            "Generate professional, well-structured support reports that document the "
            "entire process: initial issue, diagnosis, solution applied, steps performed, "
            "and recommendations. The report must be suitable for both the client "
            "(clear, professional) and internal records (complete, detailed)."
        ),
        backstory=(
            "You are a technical writer with IT support background. You know that a good "
            "support report is a business asset: it protects against disputes, helps "
            "train new technicians, and builds client trust. Your reports are thorough, "
            "professional, and easy to read."
        ),
        tools=[generate_support_report],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    return {
        "diagnostico": diagnostico,
        "buscador": buscador,
        "solucionador": solucionador,
        "reporteador": reporteador,
    }
