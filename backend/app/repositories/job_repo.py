import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Job, JobStatus


async def create_job(
    *,
    session: AsyncSession,
    project_id: uuid.UUID,
    job_type: str,
    arq_job_id: str | None = None,
) -> Job:
    job = Job(
        project_id=project_id,
        type=job_type,
        status=JobStatus.QUEUED.value,
        arq_job_id=arq_job_id,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job_by_id(*, session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await session.get(Job, job_id)


async def get_job_by_project_id(
    *, session: AsyncSession, project_id: uuid.UUID
) -> Job | None:
    stmt = select(Job).where(Job.project_id == project_id).order_by(Job.created_at.desc())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_job_status(
    *,
    session: AsyncSession,
    job: Job,
    status: str,
    progress: dict | None = None,
    error: str | None = None,
) -> Job:
    job.status = status
    if progress is not None:
        job.progress = progress
    if error is not None:
        job.error = error
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job