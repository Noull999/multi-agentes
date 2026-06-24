"""Task definitions for Code Review Bot."""

from crewai import Task


def create_tasks(agents, target_dir):
    """Crea las tareas del pipeline de revisión de código."""

    analyze_code = Task(
        description=(
            f"Analyze the source code in the directory '{target_dir}'. "
            "Use ReadSourceFiles and ListFilesInRepo tools to understand the project structure. "
            "Identify: main entry points, architecture pattern used, key dependencies, "
            "module organization, and data flow. Provide a structured architectural overview."
        ),
        expected_output=(
            "A structured analysis including: project structure overview, architecture pattern, "
            "main components and their responsibilities, data flow description, dependency list, "
            "and any architectural concerns."
        ),
        agent=agents["code_analyzer"],
    )

    hunt_bugs = Task(
        description=(
            f"Examine the source code in '{target_dir}' for bugs, security issues, and errors. "
            "Use ReadSourceFiles to read files. Look for: null/undefined access, "
            "improper error handling, security vulnerabilities (XSS, injection, exposed keys), "
            "race conditions, memory issues, unhandled edge cases, type mismatches, "
            "and logic errors. Be specific: cite file names and line numbers."
        ),
        expected_output=(
            "A categorized list of issues found: CRITICAL (security, data loss), "
            "HIGH (logic errors, crashes), MEDIUM (edge cases, potential errors), "
            "LOW (warnings, minor issues). Each with file path, line reference, and fix suggestion."
        ),
        agent=agents["bug_hunter"],
    )

    review_style = Task(
        description=(
            f"Review the code style and best practices in '{target_dir}'. "
            "Use ReadSourceFiles and ListFilesInRepo to examine the code. Check for: "
            "consistent naming conventions, proper file organization, function/component sizes, "
            "proper use of framework features (React hooks patterns, Next.js conventions), "
            "code smells (duplicated code, large functions, too many props), "
            "and adherence to TypeScript strictness. Suggest concrete refactors."
        ),
        expected_output=(
            "A report organized by: naming conventions, file organization, component design, "
            "code smells, TypeScript practices, and framework-specific recommendations. "
            "Each point should include the file reference and a concrete improvement suggestion."
        ),
        agent=agents["style_reviewer"],
    )

    generate_report = Task(
        description=(
            "Synthesize all previous analysis results into a comprehensive review report. "
            "Use GenerateReviewReport to create the final output. The report should include: "
            "1) Executive summary with overall score/verdict, "
            "2) Architecture overview, "
            "3) Bugs and security issues (prioritized), "
            "4) Style and best practices feedback, "
            "5) Documentation gaps, "
            "6) Actionable recommendations ordered by priority. "
            "Format as professional markdown with clear sections and severity badges."
        ),
        expected_output=(
            "A complete markdown report saved to a file, containing all findings organized "
            "by severity and category. The report must be actionable and professional."
        ),
        agent=agents["documenter"],
        context=[analyze_code, hunt_bugs, review_style],
    )

    return [analyze_code, hunt_bugs, review_style, generate_report]
