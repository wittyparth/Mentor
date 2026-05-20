from redis.asyncio import Redis

from app.core.config import settings

redis_pool: Redis | None = None


async def get_redis_pool() -> Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return redis_pool


async def close_redis_pool() -> None:
    global redis_pool
    if redis_pool is not None:
        await redis_pool.aclose()
        redis_pool = None