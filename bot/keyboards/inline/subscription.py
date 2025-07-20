from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.models.models import Subscription

def get_subscription_keyboard(subscriptions: list[Subscription], i18n: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=sub.name, callback_data=f"subscribe:{sub.id}")]
        for sub in subscriptions
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
