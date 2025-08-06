from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_settings_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get("referral.title", "Реферальный код"), callback_data="settings:referral")],
        [InlineKeyboardButton(text=i18n.get("settings.edit_name", "Изменить имя"), callback_data="settings:edit_name")],
        [InlineKeyboardButton(text=i18n.get("settings.email", "Email"), callback_data="settings:email")],
        [InlineKeyboardButton(text=i18n["settings.language"], callback_data="settings:language")],
    ])


def get_simple_settings_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Упрощенная клавиатура настроек для профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get("referral.input_button", "Ввести реферальный код"), callback_data="referral:input")],
        [InlineKeyboardButton(text=i18n.get("settings.edit_name", "Изменить имя"), callback_data="settings:edit_name")],
        [InlineKeyboardButton(text=i18n["settings.language"], callback_data="settings:language")],
    ])

def get_language_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура для выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language:set:ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="language:set:en")],
        [InlineKeyboardButton(
            text="🔙 " + i18n.get("back", "Назад"), 
            callback_data="settings:back"
        )]
    ])

def get_timezone_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура для выбора часового пояса"""
    timezones = [
        ("🇷🇺 Москва (UTC+3)", "Europe/Moscow"),
        ("🇺🇸 Нью-Йорк (UTC-5)", "America/New_York"),
        ("🇺🇸 Лос-Анджелес (UTC-8)", "America/Los_Angeles"),
        ("🇬🇧 Лондон (UTC+0)", "Europe/London"),
        ("🇩🇪 Берлин (UTC+1)", "Europe/Berlin"),
        ("🇫🇷 Париж (UTC+1)", "Europe/Paris"),
        ("🇯🇵 Токио (UTC+9)", "Asia/Tokyo"),
        ("🇨🇳 Пекин (UTC+8)", "Asia/Shanghai"),
        ("🇦🇺 Сидней (UTC+10)", "Australia/Sydney"),
        ("🇧🇷 Сан-Паулу (UTC-3)", "America/Sao_Paulo")
    ]
    
    keyboard = []
    for display_name, tz_name in timezones:
        keyboard.append([InlineKeyboardButton(
            text=display_name, 
            callback_data=f"timezone:set:{tz_name}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="🔙 " + i18n.get("back", "Назад"), 
        callback_data="settings:back"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notifications_keyboard(i18n: dict, current_settings: dict) -> InlineKeyboardMarkup:
    """Клавиатура для настройки уведомлений"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📝 {'✅' if current_settings.get('notify_new_posts', True) else '❌'} " + i18n.get("settings.notify_new_posts", "Новые посты"),
            callback_data="notifications:toggle:new_posts"
        )],
        [InlineKeyboardButton(
            text=f"📅 {'✅' if current_settings.get('notify_scheduled', True) else '❌'} " + i18n.get("settings.notify_scheduled", "Запланированные посты"),
            callback_data="notifications:toggle:scheduled"
        )],
        [InlineKeyboardButton(
            text=f"🔔 {'✅' if current_settings.get('notify_errors', True) else '❌'} " + i18n.get("settings.notify_errors", "Ошибки"),
            callback_data="notifications:toggle:errors"
        )],
        [InlineKeyboardButton(
            text=f"💰 {'✅' if current_settings.get('notify_payments', True) else '❌'} " + i18n.get("settings.notify_payments", "Платежи"),
            callback_data="notifications:toggle:payments"
        )],
        [InlineKeyboardButton(
            text="🔙 " + i18n.get("back", "Назад"), 
            callback_data="settings:back"
        )]
    ])


def get_email_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура для настроек email"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 " + i18n.get("settings.enter_email", "Ввести email"),
            callback_data="email:enter"
        )],
        [InlineKeyboardButton(
            text="🔙 " + i18n.get("back", "Назад"), 
            callback_data="settings:back"
        )]
    ])


def get_referral_keyboard(i18n: dict, referral_code: str = None) -> InlineKeyboardMarkup:
    """Клавиатура для настроек реферального кода"""
    keyboard = []
    
    if referral_code:
        # Кнопка для копирования реферального кода
        keyboard.append([InlineKeyboardButton(
            text="📋 " + i18n.get("referral.copy", "Скопировать код"),
            callback_data=f"referral:copy:{referral_code}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="🔙 " + i18n.get("back", "Назад"), 
        callback_data="settings:back"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
