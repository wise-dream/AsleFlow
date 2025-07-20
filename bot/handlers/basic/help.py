from aiogram.types import Message
from aiogram.filters import Command

def register_help_handler(router):
    router.message.register(help_handler, Command("help"))

async def help_handler(message: Message, i18n, locale):
    await message.answer(i18n.get("help"))

__all__ = ["register_help_handler"]
