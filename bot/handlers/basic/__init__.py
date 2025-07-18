from aiogram import Router
from .start import register_start_handlers
# from .profile import register_profile_handlers
# from .language import register_language_handlers

def register_basic_handlers(dp):
    router = Router()
    register_start_handlers(router)
    # register_profile_handlers(router)
    # register_language_handlers(router)
    dp.include_router(router)