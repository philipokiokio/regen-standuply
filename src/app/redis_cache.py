import redis
from src.app.config import redis_settings

# Create a Redis client
redis_client = redis.Redis(
    host=redis_settings.host, port=redis_settings.port, db=redis_settings.db
)
