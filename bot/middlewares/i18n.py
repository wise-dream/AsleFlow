from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from typing import Any, Callable, Awaitable, Dict
import os
import json
import logging

logger = logging.getLogger(__name__)

class I18nMiddleware(BaseMiddleware):
    def __init__(self, default_locale='en'):
        self.default_locale = default_locale
        self.locales_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'locales'))
        self.translations = {}
        self._load_locales()

    def _load_locales(self):
        if not os.path.exists(self.locales_path):
            logger.warning(f"Locales folder does not exist: {self.locales_path}")
            return

        for fname in os.listdir(self.locales_path):
            if fname.endswith('.json'):
                lang = fname.split('.')[0]
                try:
                    with open(os.path.join(self.locales_path, fname), encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    logger.exception(f"Failed to load translation for {lang}: {e}")

    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        message: Message = data.get('event_message') or getattr(event, 'message', None)

        # 1. Попробовать из профиля пользователя
        user_lang = data.get("user").language if data.get("user") and getattr(data["user"], "language", None) else None

        # 2. Или из Telegram профиля
        if not user_lang and message and message.from_user and message.from_user.language_code:
            user_lang = message.from_user.language_code[:2]

        # 3. Или дефолт
        if user_lang not in self.translations:
            user_lang = self.default_locale

        data['locale'] = user_lang
        data['i18n'] = self.translations.get(user_lang, {})

        return await handler(event, data)
