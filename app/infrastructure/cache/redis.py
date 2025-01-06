import redis


class RedisClient:
    def __init__(self, redis_url: str):
        self._redis = redis.StrictRedis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> str:
        return self._redis.get(key)

    def set(self, key: str, value: str, expire: int = None):
        self._redis.set(key, value, ex=expire)

    def delete(self, key: str):
        self._redis.delete(key)

