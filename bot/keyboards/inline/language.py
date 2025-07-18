from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🇷🇺 Русский', callback_data='set_lang:ru'),
            InlineKeyboardButton(text='🇬🇧 English', callback_data='set_lang:en'),
        ]
    ])
    return keyboard 