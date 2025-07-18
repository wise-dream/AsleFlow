from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from typing import Callable, Awaitable, Dict, Any
import os
import json

class I18nMiddleware(BaseMiddleware):
    def __init__(self, default_locale='en'):
        self.default_locale = default_locale
        # Абсолютный путь к папке bot/locales
        self.locales_path = os.path.join(os.path.dirname(__file__), '..', 'locales')
        self.locales_path = os.path.abspath(self.locales_path)
        self.translations = {}
        self._load_locales()

    def _load_locales(self):
        for fname in os.listdir(self.locales_path):
            if fname.endswith('.json'):
                lang = fname.split('.')[0]
                with open(os.path.join(self.locales_path, fname), encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)

    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        message: Message = data.get('event_message') or getattr(event, 'message', None)
        user_lang = self.default_locale
        if message and message.from_user and hasattr(message.from_user, 'language_code'):
            user_lang = message.from_user.language_code[:2]
        if user_lang not in self.translations:
            user_lang = self.default_locale
        data['locale'] = user_lang
        data['i18n'] = self.translations.get(user_lang, {})
        return await handler(event, data)
