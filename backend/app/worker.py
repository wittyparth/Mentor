from arq.connections import RedisSettings

from app.core.config import settings


async def on_startup(ctx):
    from app.core.database import AsyncSessionLocal
    from app.core.redis import get_redis_pool

    ctx["db_session_factory"] = AsyncSessionLocal
    ctx["redis"] = await get_redis_pool()


async def on_shutdown(ctx):
    from app.core.redis import close_redis_pool

    await close_redis_pool()


async def research_pipeline_task(ctx, project_id: str):
    from app.jobs.research_job import research_pipeline_task as _research
    return await _research(ctx, project_id)


async def linear_push_task(ctx, project_id: str):
    from app.jobs.linear_push_job import linear_push_task as _push
    return await _push(ctx, project_id)


class WorkerSettings:
    functions = [research_pipeline_task, linear_push_task]
    cron_jobs = []
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10
    job_timeout = 300