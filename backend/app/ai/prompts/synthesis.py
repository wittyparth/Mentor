def build_synthesis_prompt(
    stack_decisions: list[dict],
    search_results: str,
    project_idea: str,
    skill_level: str = "knows_basics",
    constraints: dict | None = None,
) -> list[dict]:
    system = (
        "You synthesize research into a project brief. "
        "Rules on feature scoping: Be honest about what fits in the timeline. "
        "Beginners spend 30-50% more time than experts. "
        "Core functionality first. Only link to official docs or well-known tutorials. "
        f"Skill level: {skill_level}."
    )

    user_msg = f"Project: {project_idea}\n\n"
    user_msg += "Stack decisions:\n"
    for d in stack_decisions:
        user_msg += f"- {d.get('category', '')}: {d.get('recommended', '')} — {d.get('rationale', '')}\n"
    user_msg += f"\nResearch results:\n{search_results}\n"
    if constraints:
        user_msg += f"\nConstraints: {constraints}\n"
    user_msg += "\nSynthesize this into a research brief with feature scoping."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]