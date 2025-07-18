from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bot import config

# Асинхронный движок и сессии SQLAlchemy
engine = create_async_engine(config.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Асинхронное подключение к Redis
import redis.asyncio as aioredis

async def get_redis():
    return aioredis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD,
        decode_responses=True
    )