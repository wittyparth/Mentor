from arq.connections import _pool_from_url

from app.core.config import settings


async def enqueue_arq_job(
    func_name: str,
    *args,
    _job_id: str | None = None,
    _max_tries: int | None = None,
    _job_timeout: int | None = None,
    _keep_result: int | None = None,
    _retry_time: int | None = None,
    **kwargs,
) -> str | None:
    redis = await _pool_from_url(settings.REDIS_URL)
    try:
        job_id = await redis.enqueue_job(
            func_name,
            *args,
            _job_id=_job_id,
            _max_tries=_max_tries,
            _job_timeout=_job_timeout,
            _keep_result=_keep_result,
            _retry_time=_retry_time,
            **kwargs,
        )
        return job_id
    finally:
        await redis.aclose()