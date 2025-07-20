from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.services.crud.user import get_user_by_telegram_id

def register_about_handler(router):
    router.message.register(about_handler, Command("about"))

async def about_handler(message: Message, state: FSMContext, session, i18n, locale):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        await message.answer(i18n.get('user_not_found'))
        return

    info = (
        f"ID: {user.telegram_id}\n"
        f"Name: {getattr(user, 'name', '-') or '-'}\n"
        f"Username: @{user.username if user.username else '-'}\n"
        f"Language: {str(user.language).upper() or '-'}\n"
    )

    about_text = i18n.get('about_user').format(info=info)
    await message.answer(about_text)


__all__ = ["register_about_handler"] 