from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.models.models import SocialAccount  # или нужный импорт, если у тебя по-другому

def get_confirm_admin_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=i18n.get("accounts.telegram.confirm_admin_button", "✅ I added the bot as admin"),
            callback_data="add:telegram:confirm"
        )]
    ])


def get_accounts_keyboard(i18n: dict, accounts: list[SocialAccount]) -> InlineKeyboardMarkup:
    keyboard = []

    for acc in accounts:
        name = acc.channel_name or "-"
        platform = acc.platform.upper() if acc.platform else "-"
        button = InlineKeyboardButton(
            text=f"{name} ({platform})",
            callback_data=f"accounts:view:{acc.id}"
        )
        keyboard.append([button])

    # Кнопка "Добавить аккаунт"
    keyboard.append([
        InlineKeyboardButton(
            text=i18n["accounts.button.add"],
            callback_data="accounts:add"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_platforms_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Telegram", callback_data="add:telegram")],
    ])

def get_manage_account_keyboard(i18n: dict, acc_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("accounts.button.rename", "✏️ Rename"),
                callback_data=f"accounts:edit:{acc_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("accounts.button.delete", "🗑️ Delete"),
                callback_data=f"accounts:delete:{acc_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("common.back", "⬅️ Back"),
                callback_data="accounts:back"
            )
        ]
    ])