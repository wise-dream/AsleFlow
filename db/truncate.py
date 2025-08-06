import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://admin:asleflow$db$pas@95.181.162.71:5432/asleflowdb"

SEED_PLANS = [
    {
        "name": "Basic",
        "price": 599.00,
        "channels_limit": 1,
        "posts_limit": 30,
        "manual_posts_limit": 10,
        "ai_priority": False,
        "description": "Подходит для начинающих. 1 канал, 30 постов в месяц, 10 ручных постов.",
        "is_active": True
    },
    {
        "name": "Pro",
        "price": 1199.00,
        "channels_limit": 3,
        "posts_limit": 100,
        "manual_posts_limit": 30,
        "ai_priority": True,
        "description": "Для активных пользователей. До 3 каналов, 100 постов, 30 ручных постов и приоритетный AI.",
        "is_active": True
    },
    {
        "name": "Business",
        "price": 2999.00,
        "channels_limit": 10,
        "posts_limit": 500,
        "manual_posts_limit": 100,
        "ai_priority": True,
        "description": "Максимальные возможности для бизнеса. 10 каналов, 500 постов, 100 ручных постов и высокий приоритет AI.",
        "is_active": True
    },
]

async def truncate_and_seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Получаем список таблиц
        tables = await conn.run_sync(
            lambda sync_conn: list(
                sync_conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version';"
                ))
            )
        )

        table_names = [row[0] for row in tables]

        if table_names:
            tables_str = ', '.join([f'"{t}"' for t in table_names])
            await conn.execute(text(f'TRUNCATE {tables_str} RESTART IDENTITY CASCADE;'))
            print(f"✅ Очистка завершена. Таблицы: {tables_str}")
        else:
            print("⚠️ Нет таблиц для очистки.")

        # Вставляем дефолтные планы
        for plan in SEED_PLANS:
            await conn.execute(
                text("""
                    INSERT INTO plans 
                    (name, price, channels_limit, posts_limit, manual_posts_limit, ai_priority, description, is_active)
                    VALUES (:name, :price, :channels_limit, :posts_limit, :manual_posts_limit, :ai_priority, :description, :is_active)
                """),
                plan
            )

        print("✅ Сидинг планов выполнен.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(truncate_and_seed())
