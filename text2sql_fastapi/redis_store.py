import redis.asyncio as aioredis
from config import settings

JIT_EXPIRY = 3600

"""
Async Redis utility functions for JWT blocklist and prompt template storage.
Handles token blacklisting and prompt template caching for user sessions.
"""

# Create Redis connection
async def get_redis_client():
    """
    Create and return an async Redis client using settings from config.
    """
    return aioredis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password)

# Add JTI (JWT ID) to blocklist with expiration
async def add_jti_to_blocklist(jti: str):
    """
    Add a JWT ID (JTI) to the Redis blocklist with an expiration time.
    """
    redis_client = await get_redis_client()
    await redis_client.set(name=jti, value="", ex=JIT_EXPIRY)

# Check if a JTI is in the blocklist
async def token_in_blocklist(jti: str) -> bool:
    """
    Check if a JWT ID (JTI) is present in the Redis blocklist.
    """
    redis_client = await get_redis_client()
    jti_value = await redis_client.get(jti)
    return jti_value is not None

# Store prompt template in Redis with user_id and session_id
async def store_prompt_template(user_id: str, session_id: str, prompt_template: str):
    """
    Store a prompt template in Redis for a given user and session.
    """
    redis_client = await get_redis_client()
    redis_key = f"prompt_template:{user_id}:{session_id}"
    await redis_client.set(redis_key, prompt_template)

# Get prompt template from Redis using user_id and session_id
async def get_prompt_template(user_id: str, session_id: str) -> str:
    """
    Retrieve a prompt template from Redis for a given user and session.
    Returns the template as a string, or None if not found.
    """
    redis_client = await get_redis_client()
    key = f"prompt_template:{user_id}:{session_id}"
    value = await redis_client.get(key)
    if value is not None:
        return value.decode("utf-8")
    return None

store = aioredis.Redis(
  host=settings.redis_host,
  port=settings.redis_port,
  password=settings.redis_password
)