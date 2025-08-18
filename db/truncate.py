import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment")

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

SEED_PROMPT_TEMPLATES = [
    {
        "name": "Базовый шаблон",
        "description": "Шаблон, учитывающий тематику и описание ситуации пользователя.",
        "template_text": (
            "Сгенерируй качественный пост для соцсетей.\n"
            "Тема: '{topic}'.\n"
            "Контекст: '{context}'.\n"
            "Цель: дать полезную ценность, удержать внимание и подтолкнуть к взаимодействию.\n"
            "Ограничения: избегай воды, пиши конкретно, используй подзаголовки/списки при необходимости.\n"
            "Стиль: {style}. Длина: {length}. Язык: {language}.\n"
            "Верни итоговый текст без лишних пояснений."
        ),
        "is_system": True,
        "is_active": True,
        "default_temperature": 0.7,
        "max_tokens": None,
    }
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

        # Вставляем системные шаблоны промптов (если есть таблица)
        try:
            for tpl in SEED_PROMPT_TEMPLATES:
                await conn.execute(
                    text("""
                        INSERT INTO prompt_templates 
                        (name, description, template_text, is_system, is_active, default_temperature, max_tokens)
                        VALUES (:name, :description, :template_text, :is_system, :is_active, :default_temperature, :max_tokens)
                    """),
                    tpl
                )
            print("✅ Сидинг prompt_templates выполнен.")
        except Exception as e:
            print(f"⚠️ Пропустил сидинг prompt_templates: {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(truncate_and_seed())
