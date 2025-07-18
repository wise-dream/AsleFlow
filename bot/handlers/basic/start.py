from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.services.user_crud import get_or_create_user
from bot.keyboards.inline.language import get_language_keyboard


async def start_handler(
    message: Message,
    state: FSMContext,
    session,
    i18n,
    locale
):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    user = await get_or_create_user(
        session=session,
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
        ref_code=None,
        default_lang='en',
    )

    user_lang = user.language or 'en'
    translations = i18n if locale == user_lang else {}
    welcome_text = translations.get('welcome')

    await message.answer(welcome_text, reply_markup=get_language_keyboard())


async def help_handler(message: Message):
    await message.answer("Help text")


def register_start_handlers(router):
    router.message.register(start_handler, Command("start"))
    router.message.register(help_handler, Command("help"))


__all__ = ["register_start_handlers"]
