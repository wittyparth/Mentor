def build_plan_generation_prompt(
    project_idea: str,
    research_brief: str,
    scoped_features: str,
    constraints: dict | None = None,
    skill_level: str = "knows_basics",
) -> list[dict]:
    system = (
        "You are a senior tech lead writing a project plan. "
        "This is the most important output of the system. "
        f"Skill level calibration: {skill_level}. "
        "Beginners: 2-3x expert speed. Intermediate: 1.5-2x.\n\n"
        "Every subtask description MUST follow this exact format:\n"
        "**What this is:** [1-2 sentences plain English]\n"
        "**Why in this order:** [1 sentence — what would break if done later]\n"
        "**Steps:** [numbered, with actual commands and code snippets]\n"
        "**Beginner trap:** [the one specific mistake that costs hours]\n"
        "**Verify it worked:** [how to confirm the task is complete]\n"
        "**If stuck, search:** \"[specific quoted Google query]\"\n\n"
        "Sprint goals are outcome statements: 'By the end of this sprint, you should be able to...'"
    )

    user_msg = f"Project idea: {project_idea}\n\n"
    user_msg += f"Research brief:\n{research_brief}\n\n"
    user_msg += f"Scoped features:\n{scoped_features}\n"
    if constraints:
        total_hours = constraints.get("total_hours_available", 0) or (
            (constraints.get("hours_per_week", 7) or 7)
            * (constraints.get("timeline_weeks", 8) or 8)
        )
        user_msg += f"\nTotal hours: {total_hours}, Hours/week: {constraints.get('hours_per_week', 7)}\n"
        user_msg += f"Planning style: {constraints.get('planning_style', 'sprint_based')}\n"

    user_msg += "\nGenerate the full project plan with epics, stories, subtasks, and sprint assignments."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]