def build_clarification_prompt(
    entry_type: str,
    raw_idea: str | None = None,
    tech_stack: dict | None = None,
    skill_level: str | None = None,
    constraints: dict | None = None,
) -> list[dict]:
    system = (
        "You are a senior engineer evaluating a project brief before planning. "
        "Your job is to identify gaps, ambiguities, and missing critical information. "
        "Rules: Only ask if the answer would meaningfully change the plan. "
        "Max 4 questions. Never ask about things that have safe defaults. "
        "Never re-ask what was already answered in the constraints. "
        "Be specific and practical. Tone: friendly, direct, like a tech lead."
    )

    context_parts = []
    if entry_type:
        context_parts.append(f"Entry type: {entry_type}")
    if raw_idea:
        context_parts.append(f"Idea: {raw_idea}")
    if tech_stack:
        context_parts.append(f"Tech stack: {tech_stack}")
    if skill_level:
        context_parts.append(f"Skill level: {skill_level}")
    if constraints:
        context_parts.append(f"Constraints: {constraints}")

    user_msg = "I need you to review this project brief and identify what's missing.\n\n"
    user_msg += "\n".join(context_parts)
    user_msg += "\n\nWhat questions should I answer before we start planning?"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]