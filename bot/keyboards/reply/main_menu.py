from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(i18n: dict) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n["menu.tasks"]), KeyboardButton(text=i18n["menu.accounts"])],
            [KeyboardButton(text=i18n["menu.posts"]), KeyboardButton(text=i18n["menu.profile"])],
            [KeyboardButton(text=i18n["menu.subscription"]), KeyboardButton(text=i18n["menu.settings"])],
        ],
        resize_keyboard=True
    )
