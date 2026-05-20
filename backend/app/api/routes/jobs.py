import json
import uuid

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.api.deps import CurrentUser, SessionDep
from app.repositories import job_repo

router = APIRouter()


@router.get("/{project_id}/sse", summary="SSE stream for job progress")
async def job_sse_stream(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> EventSourceResponse:
    from app.core.redis import get_redis_pool

    redis = await get_redis_pool()
    channel = f"devmentor:progress:{project_id}"

    job = await job_repo.get_job_by_project_id(session=session, project_id=project_id)

    async def event_generator():
        if job:
            yield {
                "event": "progress",
                "data": json.dumps({
                    "stage": (job.progress or {}).get("stage", ""),
                    "done": (job.progress or {}).get("done", 0),
                    "total": (job.progress or {}).get("total", 0),
                    "message": (job.progress or {}).get("message", ""),
                }),
            }

        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    parsed = json.loads(data)

                    yield {"event": "progress", "data": data}

                    event_type = parsed.get("event", "")
                    if event_type in ("complete", "jira_complete", "failed"):
                        break
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return EventSourceResponse(
        event_generator(),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{project_id}/status", summary="Get job status for a project")
async def job_status(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    from app.schemas.project import JobPublic

    job = await job_repo.get_job_by_project_id(session=session, project_id=project_id)
    if not job:
        return {"status": "not_found", "progress": None}
    return JobPublic.model_validate(job).model_dump()