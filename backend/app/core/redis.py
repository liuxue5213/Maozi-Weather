import redis.asyncio as redis
from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=20,
)


async def get_redis() -> redis.Redis:
    """获取 Redis 连接"""
    return redis.Redis(connection_pool=redis_pool)
