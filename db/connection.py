from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bot import config
import logging

logger = logging.getLogger(__name__)

# Асинхронный движок и сессии SQLAlchemy с улучшенными настройками
engine = create_async_engine(
    config.DATABASE_URL, 
    echo=False, 
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Пересоздание соединений каждый час
    pool_timeout=30,     # Таймаут получения соединения
    max_overflow=10,     # Максимальное количество дополнительных соединений
    pool_size=5          # Размер пула соединений
)

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

async def test_db_connection():
    """Тестирует подключение к базе данных"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text('SELECT 1'))
            logger.info("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False