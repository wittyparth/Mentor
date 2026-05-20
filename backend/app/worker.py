from arq import cron
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


class WorkerSettings:
    functions = []
    cron_jobs = []
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10
    job_timeout = 300