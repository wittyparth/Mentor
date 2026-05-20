def build_query_generation_prompt(
    project_idea: str,
    skill_level: str = "knows_basics",
    complete_stack: list[str] | None = None,
    gaps: list[str] | None = None,
) -> list[dict]:
    system = (
        "You generate precise web search queries for researching a software project. "
        "Rules: Be specific — include version numbers and years (e.g. 'Next.js 14 App Router 2024'). "
        "Include 'beginner' or 'step by step' for beginners. "
        "Cover: official docs, best practices, common mistakes, time estimates, deployment. "
        "Generate 10-14 queries. Each query should target a specific aspect of the stack."
    )

    user_msg = f"Project: {project_idea}\n"
    user_msg += f"Skill level: {skill_level}\n"
    if complete_stack:
        user_msg += f"Complete stack: {', '.join(complete_stack)}\n"
    if gaps:
        user_msg += f"Gaps to research: {', '.join(gaps)}\n"
    user_msg += "\nGenerate search queries."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]