from pydantic import BaseModel, Field


class Subtask(BaseModel):
    summary: str = Field(..., max_length=100, description="Action-oriented title, max 10 words")
    description: str = Field(..., description="Full description with steps, traps, verify steps")
    estimated_hours: float = Field(..., description="Estimated hours for this subtask")


class Story(BaseModel):
    summary: str = Field(..., description="User-facing story in 'As a...' format")
    description: str = Field(..., description="Acceptance criteria and context")
    story_points: int = Field(..., description="Fibonacci: 1, 2, 3, 5, 8, 13")
    priority: str = Field(..., description="Highest | High | Medium | Low")
    sprint_number: int = Field(..., description="Which sprint this story belongs to")
    epic_id: str = Field(..., description="Reference to parent epic ID")
    subtasks: list[Subtask] = Field(default_factory=list)


class Sprint(BaseModel):
    number: int
    name: str = Field(..., description="e.g. 'Sprint 1 — Foundation'")
    goal: str = Field(..., description="Outcome statement starting with 'By the end of this sprint...'")
    story_ids: list[str] = Field(default_factory=list)
    duration_weeks: int = 2


class Epic(BaseModel):
    id: str = Field(..., description="e.g. 'epic_1'")
    name: str = Field(..., description="e.g. 'Authentication System'")
    description: str = ""
    color: str = "blue"


class FullPlan(BaseModel):
    epics: list[Epic] = Field(default_factory=list)
    stories: list[Story] = Field(default_factory=list)
    sprints: list[Sprint] = Field(default_factory=list)
    total_estimated_hours: float = 0
    plan_summary: str = ""