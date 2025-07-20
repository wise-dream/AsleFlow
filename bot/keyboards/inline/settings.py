from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_settings_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n["settings.language"], callback_data="settings:language")],
        [InlineKeyboardButton(text=i18n["settings.notifications"], callback_data="settings:notifications")],
        [InlineKeyboardButton(text="📝 Редактировать профиль", callback_data="settings:edit_profile")]
    ])