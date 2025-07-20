from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_social_accounts_keyboard(accounts: list[dict], i18n: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=f"{acc['platform']} - {acc['username']}", callback_data=f"account:{acc['id']}")]
        for acc in accounts
    ]
    keyboard.append([
        InlineKeyboardButton(text=i18n["account.add"], callback_data="account:add")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
