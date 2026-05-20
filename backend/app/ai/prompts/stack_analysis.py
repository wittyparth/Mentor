def build_stack_analysis_prompt(
    project_idea: str,
    mentioned_stack: list[str] | None = None,
    clarification_qa: list[dict] | None = None,
    skill_level: str = "knows_basics",
) -> list[dict]:
    system = (
        "You are a technical architect completing a project's technology stack. "
        "Calibrate recommendations to the skill level explicitly: "
        "beginners → simplest thing that works (Clerk over custom auth, Prisma over raw SQL); "
        "intermediate → industry standard. "
        "Never recommend bleeding-edge or poorly-documented tools. "
        "Output a complete stack with rationale for each decision."
    )

    user_msg = f"Project idea: {project_idea}\n\n"
    if mentioned_stack:
        user_msg += f"Explicitly mentioned stack: {', '.join(mentioned_stack)}\n"
    if clarification_qa:
        user_msg += "Clarification Q&A:\n"
        for qa in clarification_qa:
            user_msg += f"Q: {qa.get('question', '')} A: {qa.get('answer', '')}\n"
    user_msg += f"\nSkill level: {skill_level}\n"
    user_msg += "\nAnalyze the stack and fill in all gaps with specific recommendations."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]