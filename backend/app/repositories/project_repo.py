import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus


async def create_project(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    entry_type: str,
    raw_idea: str | None = None,
    tech_stack: dict | None = None,
    skill_level: str | None = None,
    constraints: dict | None = None,
) -> Project:
    project = Project(
        user_id=user_id,
        entry_type=entry_type,
        raw_idea=raw_idea,
        tech_stack=tech_stack,
        skill_level=skill_level,
        constraints=constraints,
        status=ProjectStatus.DRAFT.value,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def get_project_by_id(*, session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    return await session.get(Project, project_id)


async def get_projects_by_user(
    *, session: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Project], int]:
    count_stmt = select(func.count()).select_from(Project).where(Project.user_id == user_id)
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    projects = list(result.scalars().all())
    return projects, count


async def update_project(*, session: AsyncSession, project: Project, update_data: dict) -> Project:
    for key, value in update_data.items():
        setattr(project, key, value)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project