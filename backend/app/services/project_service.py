import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectStatus
from app.repositories import project_repo
from app.schemas.project import InterviewSubmitInput, ProjectDetail, ProjectList, ProjectPublic


async def submit_interview(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    interview_data: InterviewSubmitInput,
) -> Project:
    project = await project_repo.create_project(
        session=session,
        user_id=user_id,
        entry_type=interview_data.entry_type.value,
        raw_idea=interview_data.raw_idea,
        tech_stack=interview_data.tech_stack.model_dump() if interview_data.tech_stack else None,
        skill_level=interview_data.skill_level.value if interview_data.skill_level else None,
        constraints=interview_data.constraints.model_dump() if interview_data.constraints else None,
    )
    if interview_data.clarifications:
        project = await project_repo.update_project(
            session=session,
            project=project,
            update_data={"clarifications": interview_data.clarifications},
        )
    return project


async def get_project_detail(
    *, session: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> ProjectDetail | None:
    project = await project_repo.get_project_by_id(session=session, project_id=project_id)
    if not project or project.user_id != user_id:
        return None
    return ProjectDetail.model_validate(project)


async def list_user_projects(
    *, session: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> ProjectList:
    projects, count = await project_repo.get_projects_by_user(
        session=session, user_id=user_id, skip=skip, limit=limit
    )
    return ProjectList(
        data=[ProjectPublic.model_validate(p) for p in projects], count=count
    )