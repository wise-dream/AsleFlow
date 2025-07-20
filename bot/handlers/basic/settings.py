from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.keyboards.inline.settings import get_settings_keyboard
from bot.services.crud.user import get_user_by_telegram_id

async def settings_handler(message: Message, session, i18n, locale, user):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(i18n.get("user_not_found"))
        return

    profile_info = f"👤 <b>{user.name}</b>\n🆔 {user.telegram_id}\n🌐 {user.language.upper()}"
    text = i18n.get("settings.current", "⚙️ Current task settings:\n\n{settings}").format(settings=profile_info)

    await message.answer(text, reply_markup=get_settings_keyboard(i18n))


def register_settings_handler(router):
    router.message.register(settings_handler, Command("settings"))


__all__ = ["register_settings_handler"]
