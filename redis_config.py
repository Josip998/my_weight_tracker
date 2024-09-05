import redis

# Redis configuration
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0

# Create a Redis client instance
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)
