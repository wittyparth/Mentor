import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import (
    EntryType,
    GoalType,
    JobStatus,
    JobType,
    PlanningStyle,
    ProjectStatus,
    SkillLevel,
)


class ConstraintsInput(BaseModel):
    hours_per_week: int = Field(..., ge=1, le=50)
    timeline_weeks: int | None = Field(default=None, ge=1)
    total_hours_available: int | None = None
    goal: GoalType = GoalType.ALL_OF_ABOVE
    planning_style: PlanningStyle = PlanningStyle.SPRINT_BASED


class ClarificationQuestion(BaseModel):
    question: str
    why_it_matters: str = Field(default="")
    is_critical: bool = True
    suggested_options: list[str] = Field(default_factory=list)


class ClarificationInput(BaseModel):
    entry_type: EntryType
    raw_idea: str | None = None
    tech_stack: dict | None = None
    skill_level: SkillLevel | None = None
    constraints: ConstraintsInput | None = None


class ClarificationOutput(BaseModel):
    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=4)
    confidence_assessment: str = ""


class InterviewSubmitInput(BaseModel):
    entry_type: EntryType
    raw_idea: str | None = None
    tech_stack: dict | None = None
    skill_level: SkillLevel | None = None
    constraints: ConstraintsInput | None = None
    clarifications: list[dict] = Field(default_factory=list)


class ProjectPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: str
    raw_idea: str | None = None
    entry_type: str
    skill_level: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectDetail(ProjectPublic):
    tech_stack: dict | None = None
    constraints: dict | None = None
    clarifications: list[dict] | None = None
    stack_analysis: dict | None = None
    research_brief: dict | None = None
    scoped_features: dict | None = None
    plan_json: dict | None = None
    jira_cloud_id: str | None = None
    jira_project_key: str | None = None
    jira_board_url: str | None = None


class ProjectList(BaseModel):
    data: list[ProjectPublic]
    count: int


class JobPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    status: str
    progress: dict | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobProgressEvent(BaseModel):
    stage: str
    done: int = 0
    total: int = 0
    message: str = ""