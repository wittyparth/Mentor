import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import JobType
from app.repositories import job_repo
from app.schemas.project import JobPublic


async def get_job_status(
    *, session: AsyncSession, job_id: uuid.UUID
) -> JobPublic | None:
    job = await job_repo.get_job_by_id(session=session, job_id=job_id)
    if not job:
        return None
    return JobPublic.model_validate(job)


async def get_job_by_project(
    *, session: AsyncSession, project_id: uuid.UUID
) -> JobPublic | None:
    job = await job_repo.get_job_by_project_id(session=session, project_id=project_id)
    if not job:
        return None
    return JobPublic.model_validate(job)