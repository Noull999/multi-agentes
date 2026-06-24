"""Agent definitions for Code Review Bot."""

from typing import Any, Dict, Optional

from crewai import Agent
from tools.code_reader import read_source_files
from tools.reporter import generate_review_report, list_files_in_repo


def create_agents(llm: Optional[Any] = None) -> Dict[str, Agent]:
    """Crea los 4 agentes del Code Review Bot."""

    shared_config = {}
    if llm:
        shared_config["llm"] = llm

    code_analyzer = Agent(
        role="Code Analyst",
        goal=(
            "Examine the provided source code and understand its architecture, "
            "structure, dependencies, and overall design patterns. Identify the "
            "main components, data flow, and how modules interact."
        ),
        backstory=(
            "You are a senior software architect with 15+ years of experience "
            "reviewing codebases of all sizes. You can quickly grasp the overall "
            "architecture of a project, identify its design patterns, and spot "
            "architectural weaknesses. You're particularly good at understanding "
            "TypeScript/React and Python projects."
        ),
        tools=[read_source_files, list_files_in_repo],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    bug_hunter = Agent(
        role="Bug Hunter",
        goal=(
            "Find bugs, potential errors, security vulnerabilities, and edge cases "
            "in the source code. Look for null pointer exceptions, race conditions, "
            "SQL injection, XSS, memory leaks, improper error handling, "
            "unhandled promise rejections, type errors, and logic flaws."
        ),
        backstory=(
            "You are an expert in code security and debugging. You've worked as a "
            "penetration tester and QA lead. You have a sharp eye for subtle bugs "
            "and security vulnerabilities. You never assume code is safe just "
            "because it looks clean."
        ),
        tools=[read_source_files],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    style_reviewer = Agent(
        role="Style & Best Practices Reviewer",
        goal=(
            "Review the code for style consistency, adherence to best practices, "
            "code smells, and opportunities for refactoring. Check naming conventions, "
            "file organization, function length, comment quality, and adherence to "
            "language-specific idioms and frameworks conventions."
        ),
        backstory=(
            "You are a code quality evangelist. You've written style guides for major "
            "projects and believe that clean code is the most important attribute of a "
            "maintainable system. You are strict but constructive, always suggesting "
            "concrete improvements."
        ),
        tools=[read_source_files, list_files_in_repo],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    documenter = Agent(
        role="Documentation Specialist",
        goal=(
            "Review existing documentation and suggest improvements. Identify missing "
            "documentation, outdated comments, and areas where documentation would "
            "significantly improve maintainability. Generate suggestions for README, "
            "JSDoc comments, API docs, and inline documentation."
        ),
        backstory=(
            "You are a technical writer who also codes. You believe good documentation "
            "is what separates professional projects from hobby projects. You can spot "
            "a missing JSDoc from across the room and you always have concrete "
            "suggestions for improvement."
        ),
        tools=[read_source_files, generate_review_report],
        allow_delegation=False,
        verbose=True,
        **shared_config,
    )

    return {
        "code_analyzer": code_analyzer,
        "bug_hunter": bug_hunter,
        "style_reviewer": style_reviewer,
        "documenter": documenter,
    }
