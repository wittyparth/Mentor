def build_scope_calibration_prompt(
    research_brief: str,
    constraints: dict,
    skill_level: str = "knows_basics",
) -> list[dict]:
    system = (
        "You calibrate a feature list to a fixed time budget. "
        f"Skill level: {skill_level}. Beginners take 2-3x longer than experts. "
        "Assign realistic per-feature hours. "
        "If total exceeds available hours, mark features as nice-to-have or cut. "
        "Distribute features across sprints in dependency order."
    )

    total_hours = constraints.get("total_hours_available", 0) or (
        (constraints.get("hours_per_week", 7) or 7)
        * (constraints.get("timeline_weeks", 8) or 8)
    )

    user_msg = f"Research brief:\n{research_brief}\n\n"
    user_msg += f"Total available hours: {total_hours}\n"
    user_msg += f"Hours per week: {constraints.get('hours_per_week', 7)}\n"
    user_msg += f"Planning style: {constraints.get('planning_style', 'sprint_based')}\n\n"
    user_msg += "Calibrate the feature scope and assign to sprints."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]