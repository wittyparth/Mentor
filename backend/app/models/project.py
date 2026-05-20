import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class EntryType(str, PyEnum):
    TECH_ONLY = "tech_only"
    IDEA_ONLY = "idea_only"
    BOTH = "both"


class SkillLevel(str, PyEnum):
    JUST_STARTING = "just_starting"
    KNOWS_BASICS = "knows_basics"
    COMFORTABLE = "comfortable"


class PlanningStyle(str, PyEnum):
    SPRINT_BASED = "sprint_based"
    MILESTONE_BASED = "milestone_based"
    HYBRID = "hybrid"


class GoalType(str, PyEnum):
    LEARN_TECH = "learn_tech"
    PORTFOLIO_PIECE = "portfolio_piece"
    BUILD_REAL_THING = "build_real_thing"
    ALL_OF_ABOVE = "all_of_above"


class ProjectStatus(str, PyEnum):
    DRAFT = "draft"
    RESEARCHING = "researching"
    PLANNING = "planning"
    READY = "ready"
    PUSHING = "pushing"
    PUSHED = "pushed"
    FAILED = "failed"


class JobType(str, PyEnum):
    RESEARCH_PIPELINE = "research_pipeline"
    JIRA_PUSH = "jira_push"


class JobStatus(str, PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_config"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), default=None)
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc
    )

    user: Mapped["User"] = relationship(back_populates="ai_configs")


class Project(Base):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_idea: Mapped[str | None] = mapped_column(Text, default=None)
    tech_stack: Mapped[dict | None] = mapped_column(JSONB, default=None)
    skill_level: Mapped[str | None] = mapped_column(String(20), default=None)
    constraints: Mapped[dict | None] = mapped_column(JSONB, default=None)
    clarifications: Mapped[list | None] = mapped_column(JSONB, default=list)
    stack_analysis: Mapped[dict | None] = mapped_column(JSONB, default=None)
    research_brief: Mapped[dict | None] = mapped_column(JSONB, default=None)
    scoped_features: Mapped[dict | None] = mapped_column(JSONB, default=None)
    plan_json: Mapped[dict | None] = mapped_column(JSONB, default=None)
    jira_cloud_id: Mapped[str | None] = mapped_column(String(100), default=None)
    jira_site_name: Mapped[str | None] = mapped_column(String(200), default=None)
    jira_project_key: Mapped[str | None] = mapped_column(String(50), default=None)
    jira_board_id: Mapped[int | None] = mapped_column(Integer, default=None)
    jira_board_url: Mapped[str | None] = mapped_column(String(500), default=None)
    jira_created_keys: Mapped[dict | None] = mapped_column(JSONB, default=None)
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.DRAFT.value)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc, onupdate=get_datetime_utc
    )

    user: Mapped["User"] = relationship(back_populates="projects")


class Job(Base):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    arq_job_id: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.QUEUED.value)
    progress: Mapped[dict | None] = mapped_column(JSONB, default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc, onupdate=get_datetime_utc
    )

    project: Mapped["Project"] = relationship(back_populates="jobs")


class JiraToken(Base):
    __tablename__ = "jira_token"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    cloud_id: Mapped[str] = mapped_column(String(100), nullable=False)
    site_name: Mapped[str | None] = mapped_column(String(200), default=None)
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=get_datetime_utc
    )

    user: Mapped["User"] = relationship(back_populates="jira_tokens")