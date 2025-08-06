import os
from dotenv import load_dotenv

# Всегда загружать .env из корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(DOTENV_PATH)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
LOCALES_PATH = os.getenv('LOCALES_PATH', 'locales')

# OpenAI API Key (поддерживаем оба варианта названия)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPEN_API_KEY')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

# Настройки бесплатных постов
FREE_POSTS_LIMIT = 5  # Максимальное количество бесплатных постов для новых пользователей