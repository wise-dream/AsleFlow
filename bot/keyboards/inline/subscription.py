from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.models.models import Subscription, Plan


def get_subscription_keyboard(subscriptions: list[Subscription], i18n: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=sub.name, callback_data=f"subscribe:{sub.id}")]
        for sub in subscriptions
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_balance_keyboard(i18n: dict, plans: list[Plan]) -> InlineKeyboardMarkup:
    """Клавиатура для подписок и пополнения баланса"""
    keyboard = []
    
    # Кнопка пополнения баланса
    keyboard.append([InlineKeyboardButton(
        text="💰 Пополнить баланс",
        callback_data="balance:topup"
    )])
    
    # Кнопки для подписок (если есть планы)
    if plans:
        keyboard.append([InlineKeyboardButton(
            text="📦 Доступные подписки",
            callback_data="subscription:plans"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plans_keyboard(plans: list[Plan], i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура для выбора плана подписки"""
    keyboard = []
    
    for plan in plans:
        keyboard.append([InlineKeyboardButton(
            text=f"📦 {plan.name} - {plan.price} ₽",
            callback_data=f"plan:select:{plan.id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="subscription:back"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
