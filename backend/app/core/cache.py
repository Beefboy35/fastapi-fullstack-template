import redis

from app.core.config import settings


def get_redis():
    return redis.from_url(settings.redis_url)